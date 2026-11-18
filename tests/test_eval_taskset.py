from collections import Counter
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_development_cases_are_separate_and_formal_dataset_exactly_50():
    from nutrition_eval.tasks import load_tasks, validate_taskset

    development = load_tasks(ROOT / "development_tasks.jsonl", expected_count=4)
    formal = load_tasks(ROOT / "tasks.jsonl", expected_count=50)

    validate_taskset(formal)
    assert len({task.id for task in development}) == 4
    assert {task.id for task in development}.isdisjoint(task.id for task in formal)


def test_formal_taskset_matches_approved_category_counts_and_provenance():
    from types import SimpleNamespace

    from nutrition_eval.grading import _apply_changes, grade_order, grade_state
    from nutrition_eval.state import normalize_state
    from nutrition_eval.tasks import load_tasks

    tasks = load_tasks(ROOT / "tasks.jsonl", expected_count=50)
    assert Counter(task.category for task in tasks) == {
        "nutrition": 10,
        "preparation": 8,
        "addons": 7,
        "meal_logging": 8,
        "corrections": 10,
        "queries": 5,
        "unanswerable": 2,
    }
    assert sum("edge" in task.labels for task in tasks) >= 5
    assert sum("unanswerable" in task.labels for task in tasks) == 2
    assert all(task.fixture.get("synthetic") is True for task in tasks)
    assert all(task.fixture.get("provenance", {}).get("dataset_version") == "nutrition-eval-50-v1" for task in tasks)
    assert all(task.fixture.get("catalog", {}).get("version") == "synthetic-catalog-v1" for task in tasks)
    assert all(
        ingredient.get("source", {}).get("status") == "synthetic"
        for task in tasks
        for ingredient in task.fixture["catalog"]["ingredients"]
    )
    for task in tasks:
        assert grade_state(task, normalize_state(_apply_changes(task))).passed, task.id
        interactions = []
        for rule in task.required_order:
            sequence = rule.get("sequence", [])
            if sequence:
                for name in sequence:
                    if name == "preview":
                        interactions.append({"kind": "preview", "preview_id": "preview-test"})
                    elif name == "approval":
                        interactions.append({"kind": "approval", "preview_id": "preview-test", "outcome": task.approval})
                    else:
                        interactions.append({"kind": name})
            elif rule.get("event"):
                interactions.append({"kind": rule["event"]})
        if task.expected_changes and not any(item.get("kind") == "write" for item in interactions):
            interactions.append({"kind": "write"})
        assert grade_order(task, SimpleNamespace(interactions=interactions, trace=[])).passed, task.id


def test_eval_config_freezes_clock_models_versions_and_excludes_credentials():
    from datetime import datetime
    from hashlib import sha256
    import tomllib

    from nutrition_demo.tools import TOOL_VERSION
    from nutrition_eval.judge import JUDGE_VERSION

    config = json.loads((ROOT / "eval_config.json").read_text(encoding="utf-8"))
    locked = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    openai_version = next(package["version"] for package in locked["package"] if package["name"] == "openai")

    frozen_now = datetime.fromisoformat(config["now"])
    assert frozen_now.utcoffset().total_seconds() == -8 * 60 * 60
    assert config["timezone"] == "America/Los_Angeles"
    assert config["model_id"] == "gpt-6-luna"
    assert config["judge_model_id"] == "gpt-6.1-terra"
    assert config["judge_parameters"] == {"reasoning_effort": "low", "max_output_tokens": 1024}
    assert config["judge_store"] is False
    assert config["judge_version"] == JUDGE_VERSION
    assert config["tool_version"] == TOOL_VERSION
    assert config["openai_sdk_version"] == openai_version
    assert config["dataset_version"] == config["task_version"] == "nutrition-eval-50-v1"
    assert config["formal_taskset_sha256"] == sha256((ROOT / "tasks.jsonl").read_bytes()).hexdigest()
    assert "api_key" not in config and "OPENAI_API_KEY" not in json.dumps(config)


def test_development_fixtures_seed_in_isolated_test_schemas():
    import os

    from nutrition_eval.fixtures import episode_store, seed_fixture
    from nutrition_eval.state import read_business_state
    from nutrition_eval.tasks import load_tasks

    tasks = load_tasks(ROOT / "development_tasks.jsonl", expected_count=4)
    dsn = os.environ["TEST_DATABASE_URL"]
    for task in tasks:
        with episode_store(dsn, "eval_dev") as store:
            seed_fixture(store, task.fixture)
            snapshot = read_business_state(store)
            assert len(snapshot["batches"]) == 2
            assert len(snapshot["events"]) == 3


def test_controller_receives_user_messages_without_the_answer_key(monkeypatch):
    from nutrition_demo.models import Result
    from nutrition_eval import episode as episode_module
    from nutrition_eval.tasks import load_tasks

    task = load_tasks(ROOT / "development_tasks.jsonl", expected_count=4)[0]
    task = type(task)(
        **{
            **task.__dict__,
            "scripted_answers": ["SCRIPTED-ANSWER-SENTINEL"],
            "expected_changes": [],
            "required_order": [{"event": "ANSWER-KEY-SENTINEL"}],
            "reply_rubric": ["RUBRIC-SENTINEL"],
        }
    )

    class Store:
        state = task.fixture

    class CaptureController:
        name = "capture"

        def __init__(self):
            self.messages = []

        def handle(self, message):
            self.messages.append(message)
            return Result(True, {"message": "No clarification needed."})

    controller = CaptureController()
    monkeypatch.setattr(episode_module, "read_business_state", lambda store: store.state)
    monkeypatch.setattr(episode_module, "normalize_state", lambda state: state)

    episode_module.run_episode(
        task,
        controller,
        Store(),
        repeat=1,
        now="2026-11-18T07:30:00-08:00",
        limits={},
    )

    assert controller.messages == [task.request]
    delivered = json.dumps(controller.messages)
    assert "SCRIPTED-ANSWER-SENTINEL" not in delivered
    assert "ANSWER-KEY-SENTINEL" not in delivered
    assert "RUBRIC-SENTINEL" not in delivered


class _FakeJudgeResponse:
    status = "completed"

    def __init__(self, criteria):
        self.output_text = json.dumps({"criteria": criteria})
        self.usage = None


class _FakeJudge:
    def __init__(self, *, passed=True):
        self.responses = self
        self.passed = passed

    def create(self, **_request):
        return _FakeJudgeResponse(
            [
                {"index": index, "passed": self.passed, "reason": "Synthetic development sample."}
                for index in range(1)
            ]
        )


def test_development_cases_grade_correct_and_intentionally_incorrect_samples(monkeypatch):
    from copy import deepcopy
    from nutrition_demo.models import Result
    from nutrition_eval import episode as episode_module
    from nutrition_eval.grading import _apply_changes, grade_episode, grade_reply, grade_state
    from nutrition_eval.state import normalize_state
    from nutrition_eval.tasks import load_tasks

    tasks = load_tasks(ROOT / "development_tasks.jsonl", expected_count=4)
    by_id = {task.id: task for task in tasks}

    class Store:
        def __init__(self, state):
            self.state = state

    class FakeController:
        name = "fake-controller"

        def __init__(self, task):
            self.task = task

        def handle(self, message):
            if self.task.id == "D02-correction-approval" and message == self.task.request:
                return Result(True, {
                    "action": "ask_user",
                    "arguments": {"topic": "event"},
                    "message": "Which meal should I correct?",
                    "trace": [{"type": "tool", "name": "ask_user", "arguments": {"topic": "event"}, "result": {"ok": True}}],
                })
            if self.task.id == "D02-correction-approval":
                return Result(True, {
                    "message": "Review preview-dev-2 for Nov 18 dinner.",
                    "pending_preview": "preview-dev-2",
                    "trace": [{"type": "tool", "name": "preview_correction", "arguments": {}, "result": {"ok": True}}],
                })
            if self.task.id == "D01-meal-write":
                return Result(True, {
                    "message": "The lunch was recorded.",
                    "trace": [{"type": "tool", "name": "log_meal", "arguments": {}, "result": {"ok": True}}],
                })
            return Result(True, {"message": "The answer is based on the synthetic fixture."})

        def approve(self, _preview_id, outcome):
            return Result(True, {"message": f"Synthetic approval outcome: {outcome}."})

    monkeypatch.setattr(episode_module, "read_business_state", lambda store: store.state)
    monkeypatch.setattr(episode_module, "normalize_state", normalize_state)

    for task in tasks:
        store = Store(_apply_changes(task))
        episode = episode_module.run_episode(
            task,
            FakeController(task),
            store,
            repeat=1,
            now="2026-11-18T07:30:00-08:00",
            limits={"max_model_calls": 10, "max_tool_calls": 10, "max_clarifications": 3, "timeout_seconds": 45},
        )
        assert episode.status == "complete"
        grade = grade_episode(
            task,
            episode,
            judge_client=_FakeJudge(),
            judge_config={"model_id": "fake-judge"},
        )
        assert grade.passed

    meal_task = by_id["D01-meal-write"]
    bad_store = Store(deepcopy(meal_task.fixture))
    bad_episode = episode_module.run_episode(
        meal_task,
        FakeController(meal_task),
        bad_store,
        repeat=1,
        now="2026-11-18T07:30:00-08:00",
        limits={},
    )
    bad_grade = grade_episode(
        meal_task,
        bad_episode,
        judge_client=_FakeJudge(),
        judge_config={"model_id": "fake-judge"},
    )
    assert not bad_grade.state.passed

    correction_task = by_id["D02-correction-approval"]

    class SkipsClarificationController(FakeController):
        def handle(self, _message):
            return Result(True, {
                "message": "Review preview-dev-2 for Nov 18 dinner.",
                "pending_preview": "preview-dev-2",
                "trace": [{"type": "tool", "name": "preview_correction", "arguments": {}, "result": {"ok": True}}],
            })

    bad_order_episode = episode_module.run_episode(
        correction_task,
        SkipsClarificationController(correction_task),
        Store(_apply_changes(correction_task)),
        repeat=1,
        now="2026-11-18T07:30:00-08:00",
        limits={},
    )
    bad_order_grade = grade_episode(
        correction_task,
        bad_order_episode,
        judge_client=_FakeJudge(),
        judge_config={"model_id": "fake-judge"},
    )
    assert not bad_order_grade.order.passed

    nutrition_task = by_id["D04-nutrition-edge"]
    reply_episode = type(
        "ReplyEpisode",
        (),
        {
            "reply": "The exact values are within the target bounds.",
            "interactions": [],
            "final_state": normalize_state(nutrition_task.fixture),
        },
    )()
    failed_reply = grade_reply(
        nutrition_task,
        reply_episode,
        judge_client=_FakeJudge(passed=False),
        judge_config={"model_id": "fake-judge"},
    )
    assert not failed_reply.passed
    assert failed_reply.reasons
