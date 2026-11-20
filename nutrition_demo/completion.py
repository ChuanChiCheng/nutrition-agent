"""Scoped, evidence-backed completion for existing batch/meal-target questions."""
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
import re
from uuid import uuid4

from .models import Result, encode
from .tools import SCHEMAS, DESCRIPTIONS, obj, S


COMPLETION_VERSION = 'batch-target-completion-v1'
MAX_CORRECTIONS = 2
READ_TOOLS = ('get_profile', 'batch_summary', 'find_batches', 'ask_user')
COMPLETION_SCHEMAS = {
    'assess_batch_targets': obj({'batch_id': S}),
    'finish_answer': obj({'answer_id': S}),
}
COMPLETION_DESCRIPTIONS = {
    **DESCRIPTIONS,
    'assess_batch_targets': 'Read-only: compare the requested batch per box against current meal targets. Returns request-bound answer evidence, not a completed answer.',
    'finish_answer': 'Finish this comparison only with an answer_id returned by assess_batch_targets in this request. Lookup results are not answers.',
    'ask_user': 'Pause only for a genuinely unresolved batch or missing configured meal targets.',
}
COMPLETION_INSTRUCTIONS = '''A batch-target completion contract is active. Its request and requirements are application data.
Continue choosing tools after each observation. Use assess_batch_targets for the requested batch, then finish_answer with its returned answer_id.
All four actual values, current meal targets, exact bounds, differences and overall status are required. Model prose and batch lookups cannot finish the request.
Do not guess a batch when identity is unresolved. Use ask_user topic batch, or topic profile if meal targets are missing. No writes are allowed in this read-only contract.'''


def _normal(value):
    return re.sub(r'[^\w]+', ' ', value.casefold()).strip()


def _mentions(message, value):
    if not value:return False
    suffix=r'(?!\s+targets?\b)' if _normal(value) in ('meal','daily','nutrient','nutrition') else ''
    return bool(re.search(r'\b' + re.escape(_normal(value)) + r'\b'+suffix, _normal(message)))


@dataclass(frozen=True)
class ComparisonRequest:
    source_message: str
    candidate_ids: tuple[str, ...]
    batch_id: str | None
    basis: str = 'per_box'
    target_scope: str = 'meal'


class BatchTargetCompletion:
    def __init__(self, request):
        self.request = request
        self.artifacts = {}
        self.answer = None
        self.status = 'running'
        self.corrections = 0

    @classmethod
    def from_message(cls, message, batches, *, pending=None):
        # A clarification may select only an originally offered batch. A new,
        # unrelated message must not inherit the previous comparison contract.
        if pending:
            selection = _normal(message)
            selected = [b for b in batches if b['id'] in pending['candidate_ids']
                        and selection in {_normal(b['id']), _normal(b['name'])}]
            if len(selected) == 1:
                return cls(ComparisonRequest(pending['source_message'], tuple(pending['candidate_ids']), selected[0]['id']))

        text = message.casefold()
        ids = [b for b in batches if _mentions(message, b['id'])]
        # Match longer names first so "chicken meal" does not also identify
        # a different batch named "meal". Separately mentioned names survive.
        remaining=_normal(message)
        named=set()
        for name in sorted({_normal(b['name']) for b in batches},key=len,reverse=True):
            if _mentions(remaining,name):
                named.add(name)
                remaining=re.sub(r'\b'+re.escape(name)+r'\b',' ',remaining)
        names=[b for b in batches if _normal(b['name']) in named]
        # Deliberately conservative scope: actual, single-batch, per-box meal
        # comparisons. Hypotheticals, other target scopes and writes stay on
        # their existing paths; no task IDs or evaluation rubrics are consulted.
        if not (re.search(r'\bbatch(?:es)?\b', text) or ids or names) or not re.search(r'\b(targets?|bounds?|ranges?)\b', text):
            return None
        if re.search(r'\b(if|suppose|hypothetical|would|daily|both|entire|total|addons?|whole meal|set|save|record|ate|eat|prepare|preparation|cooking|preview|correct|log|update|change|delete|remove|buy|purchase)\b|\beach\s+batch\b', text):
            return None
        if re.search(r'\b(has|had|contains?)\s+\d', text):
            return None
        if re.search(r'\b(half|quarter|double|twice)\b|\b(two|three|four|five|six|seven|eight|nine|ten|multiple|several)\s+boxes\b',text):
            return None
        if any(Decimal(quantity)!=1 for quantity in re.findall(r'\b(\d+(?:\.\d+)?)\s+box(?:es)?\b',text)):
            return None
        if ids and names and any(_normal(b['name'])!=_normal(ids[0]['name']) for b in names):
            candidates=tuple(dict.fromkeys(b['id'] for b in ids+names))
            return cls(ComparisonRequest(message,candidates,None))
        matches = ids or names
        if len(ids) > 1 or (not ids and len({_normal(b['name']) for b in names}) > 1):
            return None  # Explicit comparisons across multiple batches are separate work.
        candidates = tuple(b['id'] for b in (matches or batches))
        return cls(ComparisonRequest(message, candidates, matches[0]['id'] if len(matches)==1 else None))

    def schemas(self):
        return {**{name: SCHEMAS[name] for name in READ_TOOLS}, **COMPLETION_SCHEMAS}

    def context(self):
        return {
            'type': 'batch_target_comparison',
            'source_message': self.request.source_message,
            'batch_id': self.request.batch_id,
            'candidate_ids': self.request.candidate_ids,
            'basis': self.request.basis,
            'target_scope': self.request.target_scope,
            'required': ['four_actuals', 'four_targets', 'four_bounds', 'four_differences', 'four_statuses', 'overall_status'],
        }

    def pending(self):
        return {'source_message': self.request.source_message, 'candidate_ids': list(self.request.candidate_ids)}

    def assess(self, batch_id, service):
        if self.request.batch_id is None:
            return Result(False, {}, 'Batch identity is unresolved; ask the user to select a batch.')
        if batch_id != self.request.batch_id:
            return Result(False, {}, 'Assessment batch does not match the requested batch.')
        result = service.assess_batch_targets(batch_id)
        if not result.ok:
            return result
        answer_id = str(uuid4())
        self.artifacts[answer_id] = deepcopy(encode(result.data))
        return Result(True, {'answer_id': answer_id, 'comparison_evidence': deepcopy(self.artifacts[answer_id])})

    def finish(self, answer_id, service):
        artifact = self.artifacts.get(answer_id)
        if artifact is None:
            return Result(False, {}, 'No comparison evidence for this request. Assess the requested batch before finishing.')
        # Re-read under the service lock. This validates every computed field
        # and detects stale targets/state, missing metrics or altered evidence.
        current = service.assess_batch_targets(self.request.batch_id)
        if not current.ok or artifact != encode(current.data):
            return Result(False, {}, 'Comparison evidence is incomplete or stale; assess the requested batch again.')
        if artifact['comparison']['batch_id'] != self.request.batch_id:
            return Result(False, {}, 'Comparison evidence belongs to another batch.')
        self.answer = deepcopy(artifact['comparison'])
        self.status = 'answered'
        return Result(True, {'batch_target_answer': deepcopy(self.answer)})

    def clarification(self, topic, service):
        if topic == 'batch' and self.request.batch_id is None:
            question = 'Which batch should I compare against your meal targets?'
        elif topic == 'profile' and not service.get_profile().data.get('meal_targets'):
            question = 'Provide configured meal nutrient targets before this batch can be compared.'
        else:
            return Result(False, {}, 'The requested information is already available; produce the comparison instead.')
        self.status = 'awaiting_user'
        return Result(True, {'waiting_question': question})

    def feedback(self, reason):
        if self.corrections >= MAX_CORRECTIONS:
            self.status = 'incomplete'
            return None
        self.corrections += 1
        return {'completion_rejected': reason, 'required_next': 'Use relevant read tools or assess_batch_targets, then finish_answer; ask only for genuinely missing information.'}
