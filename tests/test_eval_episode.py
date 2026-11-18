from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone

import pytest

from nutrition_demo.models import Result
from nutrition_eval.contracts import EvalConfig, EvalTask


def make_task(**changes):
    values = {
        "id": "episode-case",
        "category": "queries",
        "labels": set(),
        "fixture": {
            "synthetic": True,
            "catalog": {"ingredients": [], "recipes": []},
            "inventory": [{"ingredient_id": "rice", "quantity": "8", "unit": "g", "state": "dry"}],
        },
        "request": "show inventory",
        "scripted_answers": [],
        "approval": None,
        "expected_changes": [],
        "required_order": [],
        "reply_rubric": [],
    }
    values.update(changes)
    return EvalTask(**values)


def make_config():
    return EvalConfig(
        now=datetime(2026, 11, 18, 7, 30, tzinfo=timezone.utc),
        model_id="gpt-6-luna",
        reasoning_effort="medium",
        max_model_calls=12,
        max_tool_calls=24,
        max_clarifications=3,
        max_output_tokens=4096,
        timeout_seconds=45,
        judge_model_id="gpt-6-luna",
        judge_parameters={},
        task_version="test-v1",
    )


class FakeStore:
    def __init__(self):
        self.state = {}


class ScriptedController:
    def __init__(self, outputs, *, pending_on_approve=None):
        self.outputs = list(outputs)
        self.messages = []
        self.approvals = []
        self.pending_on_approve = pending_on_approve

    def handle(self, message):
        self.messages.append(message)
        output = self.outputs.pop(0)
        if callable(output):
            output = output(message)
        if isinstance(output, Exception):
            raise output
        return output

    def approve(self, preview_id, outcome):
        self.approvals.append((preview_id, outcome))
        if self.pending_on_approve and preview_id != self.pending_on_approve:
            return Result(False, {}, "Confirmation must match the current pending preview")
        return Result(True, {"message": "approval handled"})


def controller_result(*, action=None, message="done", pending_preview=None, counts=None, trace=None, tool_results=None, limit_reached=False):
    data = {"message": message}
    if action:
        data["action"] = action
    if pending_preview:
        data["pending_preview"] = pending_preview
    if counts:
        data["counts"] = counts
    if trace:
        data["trace"] = trace
    if tool_results:
        data["tool_results"] = tool_results
    if limit_reached:
        data["limit_reached"] = True
    return Result(True, data)


def test_episode_replays_answer_only_after_ask_user(monkeypatch):
    import nutrition_eval.episode as episode

    monkeypatch.setattr(episode, "read_business_state", lambda _store: {})
    monkeypatch.setattr(episode, "normalize_state", lambda state: state)
    no_question = ScriptedController([controller_result(message="no question")])
    task = make_task(scripted_answers=["scripted answer"])

    skipped = episode.run_episode(task, no_question, FakeStore(), repeat=1, now=make_config().now, limits={})

    assert no_question.messages == [task.request]
    assert not any(item["kind"] == "scripted_answer" for item in skipped.interactions)

    denied_question = ScriptedController([
        controller_result(
            message="no live question",
            tool_results=[{"name": "ask_user", "result": {"ok": False, "error": "limit reached"}}],
        )
    ])
    denied = episode.run_episode(task, denied_question, FakeStore(), repeat=1, now=make_config().now, limits={})
    assert denied_question.messages == [task.request]
    assert not any(item["kind"] == "scripted_answer" for item in denied.interactions)

    asks = ScriptedController([
        controller_result(action="ask_user", message="Which batch?"),
        controller_result(message="batch-1 selected"),
    ])
    answered = episode.run_episode(task, asks, FakeStore(), repeat=1, now=make_config().now, limits={})

    assert asks.messages == [task.request, "scripted answer"]
    assert [item["kind"] for item in answered.interactions if item["kind"] in {"ask_user", "scripted_answer"}] == [
        "ask_user", "scripted_answer"
    ]

    budgeted = ScriptedController([
        controller_result(
            action="ask_user",
            message="Which batch?",
            counts={"model_calls": 12, "tool_calls": 1},
        ),
        controller_result(message="this response must not run"),
    ])
    budgeted_result = episode.run_episode(
        task,
        budgeted,
        FakeStore(),
        repeat=1,
        now=make_config().now,
        limits={"max_model_calls": 12, "max_tool_calls": 24},
    )
    assert budgeted.messages == [task.request]
    assert budgeted_result.status == "failed"
    assert budgeted_result.model_calls == 12


def test_approval_waits_for_preview_and_binds_current_id(monkeypatch):
    import nutrition_eval.episode as episode

    monkeypatch.setattr(episode, "read_business_state", lambda _store: {})
    monkeypatch.setattr(episode, "normalize_state", lambda state: state)
    task = make_task(approval="approve")

    no_preview = ScriptedController([controller_result(message="not a preview")])
    result = episode.run_episode(task, no_preview, FakeStore(), repeat=1, now=make_config().now, limits={})
    assert no_preview.approvals == []
    assert result.status == "complete"

    preview = ScriptedController(
        [controller_result(message="Review preview-1", pending_preview="preview-1")],
        pending_on_approve="preview-1",
    )
    approved = episode.run_episode(task, preview, FakeStore(), repeat=1, now=make_config().now, limits={})
    assert preview.approvals == [("preview-1", "approve")]
    assert approved.status == "complete"
    process_kinds = [
        item["kind"] for item in approved.interactions
        if item.get("kind") in {"preview", "approval", "write"}
    ]
    assert process_kinds == ["preview", "approval", "write"]

    mismatched = ScriptedController(
        [controller_result(message="Review preview-1", pending_preview="preview-1")],
        pending_on_approve="preview-other",
    )
    failed = episode.run_episode(task, mismatched, FakeStore(), repeat=1, now=make_config().now, limits={})
    assert failed.status == "failed"
    assert "preview" in failed.error.lower()

    hidden_preview = ScriptedController([
        controller_result(message="I handled it.", pending_preview="preview-hidden")
    ])
    hidden = episode.run_episode(task, hidden_preview, FakeStore(), repeat=1, now=make_config().now, limits={})
    assert hidden_preview.approvals == []
    assert not any(item["kind"] == "preview" for item in hidden.interactions)


def fake_suite_environment(monkeypatch, factory_observations):
    import nutrition_eval.episode as episode
    import nutrition_eval.runner as runner

    @contextmanager
    def episode_store(_dsn, _prefix):
        yield FakeStore()

    def seed_fixture(store, fixture):
        store.state = deepcopy(fixture)

    def read_business_state(store):
        return deepcopy(store.state)

    class MutatingController:
        def __init__(self, store):
            self.store = store

        def handle(self, _message):
            self.store.state["inventory"][0]["quantity"] = "0"
            return controller_result(
                message="changed",
                counts={"model_calls": 1, "tool_calls": 1},
                trace=[{"type": "model", "usage": {"input_tokens": 2, "output_tokens": 3}}],
            )

        def approve(self, _preview_id, _outcome):
            return Result(True, {})

    def agent_factory(store, catalog, config):
        factory_observations.append(("agent", deepcopy(store.state["inventory"]), config.now))
        return MutatingController(store)

    def baseline_factory(store, catalog, config):
        factory_observations.append(("baseline", deepcopy(store.state["inventory"]), config.now))
        return MutatingController(store)

    monkeypatch.setattr(runner, "episode_store", episode_store)
    monkeypatch.setattr(runner, "seed_fixture", seed_fixture)
    monkeypatch.setattr(episode, "read_business_state", read_business_state)
    return runner, agent_factory, baseline_factory


def test_each_repeat_reloads_same_fixture_and_clock(monkeypatch):
    observations = []
    runner, agent_factory, baseline_factory = fake_suite_environment(monkeypatch, observations)

    suite = runner.run_suite([make_task()], agent_factory, baseline_factory, make_config())

    assert suite.status == "complete"
    assert len(observations) == 4
    assert all(rows == make_task().fixture["inventory"] for _, rows, _ in observations)
    assert all(clock == make_config().now for _, _, clock in observations)


def test_suite_runs_agent_three_times_and_baseline_once(monkeypatch):
    observations = []
    runner, agent_factory, baseline_factory = fake_suite_environment(monkeypatch, observations)

    suite = runner.run_suite([make_task()], agent_factory, baseline_factory, make_config())

    assert suite.status == "complete"
    assert [episode.controller for episode in suite.episodes] == ["agent", "agent", "agent", "baseline"]
    assert [episode.repeat for episode in suite.episodes] == [1, 2, 3, 1]
    assert sum(name == "agent" for name, _, _ in observations) == 3
    assert sum(name == "baseline" for name, _, _ in observations) == 1


def test_run_suite_creates_and_cleans_real_episode_schemas():
    import os

    import psycopg
    from psycopg import sql
    from nutrition_eval.runner import run_suite

    schemas = []

    def factory(store, _catalog, _config):
        schemas.append(store.schema)
        return ScriptedController([controller_result(message="checked")])

    suite = run_suite([make_task()], factory, factory, make_config())

    assert suite.status == "complete"
    assert len(schemas) == 4
    assert len(set(schemas)) == 4
    with psycopg.connect(os.environ["TEST_DATABASE_URL"]) as connection:
        remaining = [
            schema
            for schema in schemas
            if connection.execute(
                "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name=%s)",
                (schema,),
            ).fetchone()[0]
        ]
    assert remaining == []


def test_turns_model_calls_latency_and_tokens_aggregate_across_messages(monkeypatch):
    import nutrition_eval.episode as episode

    monkeypatch.setattr(episode, "read_business_state", lambda _store: {})
    monkeypatch.setattr(episode, "normalize_state", lambda state: state)
    clock_values = iter([0.0, 0.25, 0.5, 2.0])
    monkeypatch.setattr(episode.time, "monotonic", lambda: next(clock_values))
    trace = [{"type": "model", "usage": {"input_tokens": 10, "output_tokens": 5}}]
    controller = ScriptedController([
        controller_result(action="ask_user", message="Which batch?", counts={"model_calls": 1, "tool_calls": 2}, trace=trace),
        controller_result(message="done", counts={"model_calls": 2, "tool_calls": 1}, trace=[{"type": "model", "usage": {"input_tokens": 20, "output_tokens": 7}}]),
    ])
    task = make_task(scripted_answers=["batch-1"])

    result = episode.run_episode(task, controller, FakeStore(), repeat=1, now=make_config().now, limits={})

    assert result.turns == 2
    assert result.model_calls == 3
    assert result.tool_calls == 3
    assert result.input_tokens == 30
    assert result.output_tokens == 12
    assert result.latency_ms == 1750


def test_controller_failure_is_failed_episode_but_setup_error_incompletes_suite(monkeypatch):
    import nutrition_eval.episode as episode
    import nutrition_eval.runner as runner

    monkeypatch.setattr(episode, "read_business_state", lambda _store: {})
    monkeypatch.setattr(episode, "normalize_state", lambda state: state)
    failing = ScriptedController([RuntimeError("controller broke")])
    result = episode.run_episode(make_task(), failing, FakeStore(), repeat=1, now=make_config().now, limits={})
    assert result.status == "failed"
    assert "controller broke" in result.error

    exhausted = ScriptedController([
        controller_result(
            message="limit reached",
            counts={"model_calls": 12, "tool_calls": 24},
            limit_reached=True,
        )
    ])
    exhausted_result = episode.run_episode(
        make_task(),
        exhausted,
        FakeStore(),
        repeat=1,
        now=make_config().now,
        limits={"max_model_calls": 12, "max_tool_calls": 24},
    )
    assert exhausted_result.status == "failed"
    assert exhausted_result.error == "controller resource limit reached"

    times = iter([0.0, 46.0])
    monkeypatch.setattr(episode.time, "monotonic", lambda: next(times))
    timed = ScriptedController([controller_result(message="too slow")])
    timed_result = episode.run_episode(
        make_task(),
        timed,
        FakeStore(),
        repeat=1,
        now=make_config().now,
        limits={"timeout_seconds": 45},
    )
    assert timed_result.status == "failed"
    assert timed_result.latency_ms == 46000

    observations = []
    runner, agent_factory, baseline_factory = fake_suite_environment(monkeypatch, observations)
    monkeypatch.setattr(runner, "seed_fixture", lambda _store, _fixture: (_ for _ in ()).throw(ValueError("bad fixture")))
    incomplete = runner.run_suite([make_task()], agent_factory, baseline_factory, make_config())
    assert incomplete.status == "incomplete"
    assert incomplete.episodes == []
    assert observations == []
