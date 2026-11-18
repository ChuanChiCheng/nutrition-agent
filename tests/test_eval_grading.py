import json
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from nutrition_eval.contracts import EpisodeResult, EvalTask


def grading_task(**changes):
    fixture = {
        "synthetic": True,
        "profile": {"timezone": "America/Los_Angeles"},
        "inventory": [
            {"ingredient_id": "rice", "quantity": "500", "unit": "g", "state": "dry", "source": {"status": "synthetic"}},
        ],
        "cooking_runs": [
            {"id": "run-1", "recipe_id": "curry", "prepared_on": "2026-11-17", "request_id": "seed", "data": {"note": "fixture"}},
        ],
        "batches": [
            {"id": "batch-meal", "cooking_run_id": "run-1", "name": "meal", "total_boxes": 6, "remaining_boxes": 5, "data": {"box_nutrients": {"kcal": "600"}}},
            {"id": "batch-side", "cooking_run_id": "run-1", "name": "side", "total_boxes": 2, "remaining_boxes": 2, "data": {"box_nutrients": {"kcal": "200"}}},
        ],
        "events": [
            {"id": "event-1", "batch_id": "batch-meal", "eaten_on": "2026-11-17", "meal": "dinner", "boxes": 1, "data": {"total_nutrients": {"kcal": "600"}}},
        ],
        "inventory_movements": [
            {"ingredient_id": "rice", "delta": "-100", "kind": "preparation", "cooking_run_id": "run-1", "event_id": None, "data": {"unit": "g"}},
        ],
    }
    values = {
        "id": "grade-case",
        "category": "meal_logging",
        "labels": set(),
        "fixture": fixture,
        "request": "I ate the meal batch.",
        "scripted_answers": [],
        "approval": None,
        "expected_changes": [],
        "required_order": [],
        "reply_rubric": ["Use only supported facts."],
    }
    values.update(changes)
    return EvalTask(**values)


def episode_result(*, final_state=None, interactions=None, trace=None, reply="The recorded meal has 600 kcal."):
    return EpisodeResult(
        task_id="grade-case",
        controller="agent",
        repeat=1,
        status="complete",
        reply=reply,
        trace=trace or [],
        interactions=interactions or [],
        final_state=final_state or {},
        turns=1,
        model_calls=2,
        tool_calls=1,
        input_tokens=20,
        output_tokens=5,
        latency_ms=125,
        error=None,
    )


class FakeJudgeResponse:
    status = "completed"
    model = "judge-test-model"

    def __init__(self, criteria):
        self.output_text = json.dumps({"criteria": criteria})
        self.usage = FakeUsage()


class FakeUsage:
    def model_dump(self):
        return {"input_tokens": 31, "output_tokens": 9}


class FakeJudgeClient:
    def __init__(self, criteria=None, error=None):
        self.criteria = criteria or []
        self.error = error
        self.calls = []
        self.responses = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return FakeJudgeResponse(self.criteria)


class FailsAfterOneJudgeClient:
    def __init__(self):
        self.responses = self
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return FakeJudgeResponse([{"index": 0, "passed": True, "reason": "Criterion passed."}])
        raise RuntimeError("judge service is unavailable")


def judge_config():
    return {"model_id": "judge-test-model", "max_output_tokens": 1024, "reasoning_effort": "low"}


def test_state_grader_rejects_wrong_values_and_unrelated_writes():
    from nutrition_eval.state import normalize_state
    from nutrition_eval.grading import grade_state

    from nutrition_eval.contracts import ExpectedChange

    task = grading_task(expected_changes=[ExpectedChange("update", "inventory", {"ingredient_id": "rice"}, {"quantity": "400.0"})])
    expected_raw = deepcopy(task.fixture)
    expected_raw["inventory"][0]["quantity"] = "400.0"
    correct = normalize_state(expected_raw)
    assert grade_state(task, correct).passed

    wrong_stock = deepcopy(correct)
    wrong_stock["inventory"][0]["quantity"] = "399"
    assert not grade_state(task, wrong_stock).passed

    extra_event = deepcopy(correct)
    extra_event["events"].append({"batch_id": "extra-batch", "eaten_on": "2026-11-18", "meal": "snack", "boxes": 1, "data": {"total_nutrients": {"kcal": "100"}}})
    assert not grade_state(task, extra_event).passed

    extra_movement = deepcopy(correct)
    extra_movement["inventory_movements"].append({"ingredient_id": "rice", "delta": "-1", "cooking_run_id": None, "event_id": None, "kind": "unexpected", "data": {"unit": "g"}})
    assert not grade_state(task, extra_movement).passed

    unrelated_batch = deepcopy(correct)
    unrelated_batch["batches"][1]["remaining_boxes"] = 1
    assert not grade_state(task, unrelated_batch).passed


def test_state_grader_ignores_preview_and_workflow_telemetry():
    from nutrition_eval.grading import grade_state
    from nutrition_eval.state import normalize_state

    task = grading_task()
    actual = normalize_state(deepcopy(task.fixture))
    actual["previews"].append(
        {"kind": "correction", "state_version": 1, "status": "rejected", "data": {"summary": "synthetic"}}
    )
    actual["operations"].append({"input_hash": "runtime-only", "result": {"ok": True}})
    actual["workflow_sessions"].append({"data": {"stage": "preview_confirmation"}})

    assert grade_state(task, actual).passed


def test_state_grader_accepts_semantic_insert_without_database_id():
    from nutrition_eval.contracts import ExpectedChange
    from nutrition_eval.grading import grade_state
    from nutrition_eval.state import normalize_state

    event = {
        "batch_id": "batch-meal",
        "eaten_on": "2026-11-18",
        "meal": "lunch",
        "boxes": 1,
        "data": {"batch_name": "meal", "total_nutrients": {"kcal": "600"}},
    }
    task = grading_task(
        expected_changes=[
            ExpectedChange(
                "insert",
                "events",
                {"batch_id": "batch-meal", "eaten_on": "2026-11-18", "meal": "lunch", "boxes": 1},
                {"data": event["data"]},
            )
        ]
    )
    expected_raw = deepcopy(task.fixture)
    expected_raw["events"].append({"id": "generated-for-test", **event})

    assert grade_state(task, normalize_state(expected_raw)).passed


def test_order_grader_rejects_write_before_clarification_or_approval():
    from nutrition_eval.grading import grade_order

    task = grading_task(
        required_order=[{"sequence": ["ask_user", "scripted_answer", "preview", "approval", "write"]}],
        approval="approve",
    )
    valid = episode_result(
        interactions=[
            {"kind": "ask_user", "topic": "batch"},
            {"kind": "reply", "reply": "Which batch?"},
            {"kind": "scripted_answer", "message": "meal batch"},
            {"kind": "preview", "preview_id": "preview-1"},
            {"kind": "approval", "preview_id": "preview-1", "outcome": "approve"},
            {"kind": "approval_result", "ok": True},
            {"kind": "write", "preview_id": "preview-1"},
        ],
    )
    assert grade_order(task, valid).passed

    invalid = episode_result(
        interactions=[
            {"kind": "write", "action": "log_meal"},
            {"kind": "ask_user", "topic": "batch"},
            {"kind": "scripted_answer", "message": "meal batch"},
            {"kind": "preview", "preview_id": "preview-1"},
            {"kind": "approval", "preview_id": "preview-1", "outcome": "approve"},
        ],
    )
    assert not grade_order(task, invalid).passed

    missing_id = episode_result(
        interactions=[
            {"kind": "preview"},
            {"kind": "approval", "outcome": "approve"},
            {"kind": "write"},
        ],
    )
    assert not grade_order(task, missing_id).passed


def test_failed_episode_cannot_pass_even_if_final_state_matches():
    from nutrition_eval.grading import grade_episode
    from nutrition_eval.state import normalize_state

    task = grading_task()
    episode = episode_result(final_state=normalize_state(task.fixture))
    episode = EpisodeResult(**{**episode.__dict__, "status": "failed", "error": "model budget exhausted"})
    judge = FakeJudgeClient([{"index": 0, "passed": True, "reason": "The reply matches the rubric."}])

    grade = grade_episode(task, episode, judge_client=judge, judge_config=judge_config())

    assert not grade.passed
    assert not grade.order.passed
    assert "budget exhausted" in grade.order.reasons[-1]


def test_unanswerable_reply_requires_no_invention_and_no_state_change():
    from nutrition_eval.grading import grade_reply, grade_state
    from nutrition_eval.state import normalize_state

    task = grading_task(
        category="unanswerable",
        labels={"unanswerable"},
        expected_changes=[],
        reply_rubric=["Say the exact nutrition value is unavailable.", "Do not invent a meal or nutrition value."],
    )
    original = normalize_state(task.fixture)
    assert grade_state(task, original).passed

    actual = deepcopy(original)
    actual["events"].append({"batch_id": "extra-batch", "eaten_on": "2026-11-18", "meal": "lunch", "boxes": 1, "data": {"total_nutrients": {"kcal": "450"}}})
    assert not grade_state(task, actual).passed

    judge = FakeJudgeClient([
        {"index": 0, "passed": False, "reason": "The answer did not state that the value is unavailable."},
        {"index": 1, "passed": False, "reason": "The answer invented 450 kcal."},
    ])
    reply_grade = grade_reply(
        task,
        episode_result(final_state=actual, reply="It was 450 kcal."),
        judge_client=judge,
        judge_config=judge_config(),
    )
    assert not reply_grade.passed
    assert len(reply_grade.reasons) == 2


def test_reply_judge_parses_each_rubric_criterion_and_excludes_usage():
    from nutrition_eval.grading import grade_episode
    from nutrition_eval.state import normalize_state

    task = grading_task(reply_rubric=["State the inventory quantity.", "Do not claim the write was approved."])
    episode = episode_result(final_state=normalize_state(task.fixture))
    judge = FakeJudgeClient([
        {"index": 0, "passed": True, "reason": "The quantity matches the fixture."},
        {"index": 1, "passed": False, "reason": "The answer claimed approval."},
    ])

    grade = grade_episode(task, episode, judge_client=judge, judge_config=judge_config())

    assert not grade.passed
    assert not grade.reply.passed
    assert grade.judge_usage["input_tokens"] == 31
    assert grade.judge_usage["output_tokens"] == 9
    assert grade.judge_usage["latency_ms"] >= 0
    assert (episode.model_calls, episode.input_tokens, episode.output_tokens) == (2, 20, 5)
    request = judge.calls[0]
    assert request["model"] == "judge-test-model"
    assert request["reasoning"] == {"effort": "low"}
    assert request["max_output_tokens"] == 1024
    assert request["store"] is False
    assert request["text"]["format"]["strict"] is True
    prompt = json.dumps(request["input"], ensure_ascii=False)
    assert "expected_changes" not in prompt
    assert "State the inventory quantity." in prompt


def test_judge_outage_marks_suite_incomplete_without_final_metrics():
    from nutrition_eval.grading import JudgeUnavailable, grade_suite
    from nutrition_eval.contracts import SuiteResult
    from nutrition_eval.state import normalize_state

    task = grading_task()
    state = normalize_state(task.fixture)
    suite = SuiteResult(
        "complete",
        [episode_result(final_state=state), episode_result(final_state=state)],
    )
    judge = FailsAfterOneJudgeClient()

    with pytest.raises(JudgeUnavailable) as raised:
        grade_suite([task], suite, judge_client=judge, judge_config=judge_config())

    assert raised.value.status == "incomplete"
    assert len(raised.value.partial_results) == 1
    assert not hasattr(raised.value, "summary")
    assert "judge service is unavailable" in str(raised.value)
