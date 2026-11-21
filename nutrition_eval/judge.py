"""Frozen structured rubric judge; it never participates in controller decisions."""
import json
import jsonschema
import time
from decimal import Decimal, InvalidOperation

from .contracts import GradePart


JUDGE_VERSION = "nutrition-reply-judge-v2"
REPLY_GRADER_VERSION = "nutrition-reply-grader-v1"
JUDGE_INSTRUCTIONS = """You are an independent evaluator. Score only the listed response criteria using the provided fixture, conversation, controller reply, and actual final state.
Do not invent facts. Do not use or infer hidden expected_changes or process order. For each numbered criterion return exactly one result with the same index, a boolean passed value, and a short reason. Return only the required JSON object."""
JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer", "minimum": 0},
                    "passed": {"type": "boolean"},
                    "reason": {"type": "string", "minLength": 1},
                },
                "required": ["index", "passed", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["criteria"],
    "additionalProperties": False,
}


def _judge_settings(config):
    if isinstance(config, dict):
        model_id = config.get("model_id", config.get("model"))
        parameters = dict(config.get("parameters", {}))
        for key in ("reasoning_effort", "max_output_tokens"):
            if key in config:
                parameters[key] = config[key]
    else:
        model_id = getattr(config, "judge_model_id", None)
        parameters = dict(getattr(config, "judge_parameters", {}) or {})
    if not isinstance(model_id, str) or not model_id:
        raise ValueError("judge model_id is required")
    max_output_tokens = parameters.pop("max_output_tokens", 1024)
    reasoning_effort = parameters.pop("reasoning_effort", None)
    if parameters:
        raise ValueError(f"unsupported frozen judge parameters: {', '.join(sorted(parameters))}")
    request = {
        "model": model_id,
        "max_output_tokens": max_output_tokens,
        "store": False,
    }
    if reasoning_effort is not None:
        request["reasoning"] = {"effort": reasoning_effort}
    return request


def _conversation(episode):
    fields = ("kind", "message", "reply", "question", "topic", "outcome")
    return [
        {key: entry[key] for key in fields if key in entry}
        for entry in episode.interactions
        if isinstance(entry, dict) and entry.get("kind") in {"request", "scripted_answer", "reply", "approval", "approval_result"}
    ]


def _usage(response):
    usage = getattr(response, "usage", None)
    if hasattr(usage, "model_dump"):
        usage = usage.model_dump()
    elif usage is not None and hasattr(usage, "__dict__"):
        usage = vars(usage)
    else:
        usage = {}
    if not isinstance(usage, dict):
        return {}
    return {
        key: int(value)
        for key, value in usage.items()
        if key in {"input_tokens", "output_tokens", "prompt_tokens", "completion_tokens"}
        and isinstance(value, int)
    }


def uses_model_judge(task) -> bool:
    """Return whether a task's reply rubric needs a model judge call."""
    return task.category != "addons"


def _exact_number(value):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if not number.is_finite():
        return None
    text = format(number, "f")
    return text.rstrip("0").rstrip(".") if "." in text else text


def _addon_preview(episode):
    for row in reversed(episode.trace):
        if not isinstance(row, dict) or row.get("name") != "preview_batch_addons":
            continue
        result = row.get("result")
        arguments = row.get("arguments")
        if not isinstance(result, dict) or result.get("ok") is not True:
            continue
        if not isinstance(arguments, dict):
            continue
        batch_id = arguments.get("batch_id")
        items = arguments.get("items")
        if isinstance(batch_id, str) and isinstance(items, list) and items:
            return batch_id, items
    return None


def _addon_names(task, batch_id, items):
    fixture = task.fixture if isinstance(task.fixture, dict) else {}
    batches = fixture.get("batches", [])
    batch_name = batch_id
    for batch in batches if isinstance(batches, list) else []:
        if not isinstance(batch, dict) or batch.get("id") != batch_id:
            continue
        data = batch.get("data") if isinstance(batch.get("data"), dict) else {}
        batch_name = batch.get("name") or batch.get("batch_name") or data.get("batch_name") or batch_id
        break

    catalog = fixture.get("catalog", {})
    ingredients = catalog.get("ingredients", []) if isinstance(catalog, dict) else []
    names = {
        item.get("id"): item.get("name", item.get("id"))
        for item in ingredients
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    } if isinstance(ingredients, list) else {}
    expected = []
    for item in items:
        if not isinstance(item, dict):
            return None
        ingredient_id = item.get("ingredient_id")
        quantity = _exact_number(item.get("quantity"))
        unit = item.get("unit")
        if not isinstance(ingredient_id, str) or ingredient_id not in names or quantity is None or not isinstance(unit, str):
            return None
        expected.append(f"{names[ingredient_id]}: {quantity} {unit}")
    return batch_name, expected


def _grade_addon_reply(task, episode) -> GradePart:
    reasons = []
    reply = episode.reply.casefold() if isinstance(episode.reply, str) else ""
    preview = _addon_preview(episode)
    if preview is None:
        return GradePart(False, ["No successful preview_batch_addons action was recorded."])

    batch_id, items = preview
    details = _addon_names(task, batch_id, items)
    if details is None:
        return GradePart(False, ["The successful addon preview could not be matched to named fixture items."])
    batch_name, expected_items = details
    expected_batch = f"{batch_name} ({batch_id})".casefold()
    if expected_batch not in reply:
        reasons.append(f"Reply omitted the addon batch {batch_name} ({batch_id}).")
    for item in expected_items:
        if item.casefold() not in reply:
            reasons.append(f"Reply omitted the exact addon quantity {item}.")

    observed_approval = next((
        row.get("outcome") for row in reversed(episode.interactions)
        if isinstance(row, dict) and row.get("kind") == "approval"
    ), None)
    if task.approval not in {"approve", "reject"} or observed_approval != task.approval:
        reasons.append("The recorded external approval outcome did not match the task.")
    elif task.approval == "approve":
        for phrase in (
            "default addon plan saved",
            "planned default",
            "stock is consumed only when eaten",
            "no meal intake was recorded",
        ):
            if phrase not in reply:
                reasons.append(f"Reply omitted the saved-default/consumption detail: {phrase}.")
    else:
        for phrase in (
            "default addon change rejected",
            "previous default plan is unchanged",
            "no intake was recorded or stock consumed",
        ):
            if phrase not in reply:
                reasons.append(f"Reply omitted the rejection detail: {phrase}.")
    return GradePart(not reasons, reasons)


def grade_reply(task, episode, *, judge_client, judge_config) -> GradePart:
    if not episode.reply:
        return GradePart(False, ["controller produced no user-facing reply"])
    if not uses_model_judge(task):
        return _grade_addon_reply(task, episode)
    request = _judge_settings(judge_config)
    payload = {
        "judge_version": JUDGE_VERSION,
        "task_id": task.id,
        "category": task.category,
        "labels": sorted(task.labels),
        "request": task.request,
        "scripted_answers_received": [
            entry.get("message")
            for entry in episode.interactions
            if isinstance(entry, dict) and entry.get("kind") == "scripted_answer"
        ],
        "conversation": _conversation(episode),
        "fixture": task.fixture,
        "actual_final_state": episode.final_state,
        "controller_reply": episode.reply,
        "criteria": [{"index": index, "text": text} for index, text in enumerate(task.reply_rubric)],
    }
    judge_started = time.monotonic()
    response = judge_client.responses.create(
        **request,
        instructions=JUDGE_INSTRUCTIONS,
        input=json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
        text={
            "format": {
                "type": "json_schema",
                "name": "nutrition_reply_grade",
                "strict": True,
                "schema": JUDGE_SCHEMA,
            }
        },
    )
    judge_latency_ms = round((time.monotonic() - judge_started) * 1000)
    if getattr(response, "status", "completed") != "completed":
        raise ValueError("judge response was incomplete")
    raw = getattr(response, "output_text", None)
    if not isinstance(raw, str) or not raw:
        raise ValueError("judge response did not contain structured JSON")
    try:
        parsed = json.loads(raw)
        jsonschema.validate(parsed, JUDGE_SCHEMA)
    except (json.JSONDecodeError, jsonschema.ValidationError) as exc:
        raise ValueError(f"judge returned invalid rubric JSON: {exc}") from exc

    results = parsed["criteria"]
    expected_indexes = list(range(len(task.reply_rubric)))
    indexes = [item["index"] for item in results]
    if len(indexes) != len(expected_indexes) or set(indexes) != set(expected_indexes):
        raise ValueError("judge must return each rubric criterion exactly once")
    reasons = []
    for item in sorted(results, key=lambda criterion: criterion["index"]):
        criterion = task.reply_rubric[item["index"]]
        if not item["passed"]:
            reasons.append(f"criterion {item['index'] + 1} failed ({criterion}): {item['reason']}")
    usage = _usage(response)
    usage["latency_ms"] = judge_latency_ms
    return GradePart(not reasons, reasons, usage=usage)
