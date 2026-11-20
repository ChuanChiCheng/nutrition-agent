"""English evaluation must preserve business semantics and English tool replies."""
import json
import re
from pathlib import Path
from datetime import datetime
import os
from nutrition_eval.tasks import load_tasks
from nutrition_eval.fixtures import episode_store, seed_fixture
from nutrition_eval.runner import _catalog_from_fixture
from nutrition_eval.controllers import agent_factory
from nutrition_eval.baseline import baseline_factory
from nutrition_eval.__main__ import _load_config

ROOT = Path(__file__).resolve().parents[1]

def test_datasets_and_evaluation_prompts_are_english():
    from nutrition_demo.agent import INSTRUCTIONS as AGENT_INSTRUCTIONS
    from nutrition_demo.tools import QUESTIONS
    from nutrition_eval.baseline import BASELINE_INSTRUCTIONS
    for filename in ('tasks.jsonl', 'development_tasks.jsonl'):
        assert not re.search(r'[\u3400-\u9fff]', (ROOT / filename).read_text())
    assert not re.search(r'[\u3400-\u9fff]', AGENT_INSTRUCTIONS + BASELINE_INSTRUCTIONS + json.dumps(QUESTIONS, ensure_ascii=False))
    assert 'English' in AGENT_INSTRUCTIONS and 'English' in BASELINE_INSTRUCTIONS

def test_shared_evaluation_operations_return_english_without_changing_meal_rules():
    task = next(t for t in load_tasks(ROOT / 'tasks.jsonl') if t.id == 'M01')
    _, config = _load_config(ROOT / 'eval_config.json')
    for factory in (agent_factory, baseline_factory):
        with episode_store(os.environ['TEST_DATABASE_URL'], 'eval_english') as store:
            seed_fixture(store, task.fixture)
            controller = factory(store, _catalog_from_fixture(task.fixture), config, client=object())
            agent = getattr(controller, 'agent', None) or controller._dispatcher
            question = agent._dispatch('ask_user', {'topic':'batch'}, 'english-ask')
            assert question.ok and question.data['waiting_question'] == 'Which batch did you eat?'
            result = agent._dispatch('log_meal', {'batch_id':'batch-1','eaten_on':'2026-11-18','meal':'lunch','addon_override':None}, 'english-meal', user_message=task.request)
            assert result.ok, result.error
            display = agent._display([{'name':'log_meal','result':{'ok':True}}])
            assert not re.search(r'[\u3400-\u9fff]', json.dumps(display, default=str, ensure_ascii=False))
            denied = agent._dispatch('log_meal', {'batch_id':'batch-1','eaten_on':'2026-11-18','meal':'lunch','addon_override':None}, 'english-question', user_message='What if I ate one box?')
            assert not denied.ok
