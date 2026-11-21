import json
from pathlib import Path

import pytest

from nutrition_eval.contracts import EpisodeGrade, EpisodeResult, EvalTask, GradePart, ScoredEpisode, SuiteResult


def scored(task_id, controller, repeat, passed, latency_ms, turns, *, model_calls=2):
    task = EvalTask(
        id=task_id,
        category="queries",
        labels=set(),
        fixture={"synthetic": True},
        request="synthetic request",
        scripted_answers=[],
        approval=None,
        expected_changes=[],
        required_order=[],
        reply_rubric=["answer accurately"],
    )
    episode = EpisodeResult(
        task_id=task_id,
        controller=controller,
        repeat=repeat,
        status="complete",
        reply="synthetic response",
        trace=[{"type": "tool", "name": "daily_summary", "arguments": {"day": "today"}}],
        interactions=[],
        final_state={"synthetic": True},
        turns=turns,
        model_calls=model_calls,
        tool_calls=1,
        input_tokens=10,
        output_tokens=5,
        latency_ms=latency_ms,
        error=None,
    )
    part = GradePart(passed, [] if passed else ["deliberate synthetic grading failure"])
    grade = EpisodeGrade(passed, part, GradePart(True, []), GradePart(True, []))
    return ScoredEpisode(task, episode, grade)


def sample_results():
    return [
        scored("T01", "agent", 1, True, 100, 1),
        scored("T01", "agent", 2, True, 200, 2),
        scored("T01", "agent", 3, True, 300, 3),
        scored("T01", "baseline", 1, True, 700, 1),
        scored("T02", "agent", 1, False, 400, 4),
        scored("T02", "agent", 2, True, 500, 5),
        scored("T02", "agent", 3, False, 600, 6),
        scored("T02", "baseline", 1, False, 800, 2),
    ]


def test_report_computes_pass_at_3_pass_power_3_flips_and_percentile():
    from nutrition_eval.report import summarize_runs

    summary = summarize_runs(sample_results())

    assert summary["controllers"]["agent"]["sample_count"] == 6
    assert summary["controllers"]["agent"]["accuracy"] == pytest.approx(4 / 6)
    assert summary["controllers"]["agent"]["mean_turns"] == pytest.approx(3.5)
    assert summary["controllers"]["agent"]["mean_model_calls"] == pytest.approx(2)
    assert summary["controllers"]["agent"]["mean_latency_ms"] == pytest.approx(350)
    assert summary["controllers"]["agent"]["p95_latency_ms"] == 600
    assert summary["controllers"]["agent"]["mean_tokens"] == pytest.approx(15)
    assert summary["controllers"]["baseline"]["sample_count"] == 2
    assert summary["controllers"]["baseline"]["accuracy"] == pytest.approx(0.5)
    assert summary["controllers"]["baseline"]["p95_latency_ms"] == 800
    assert summary["agent"]["pass_at_3"] == pytest.approx(1.0)
    assert summary["agent"]["pass_power_3"] == pytest.approx(0.5)
    assert summary["agent"]["flipped_task_ids"] == ["T02"]
    assert summary["agent"]["accuracy_by_repeat"] == {1: 0.5, 2: 1.0, 3: 0.5}


def test_report_saves_episode_samples_metadata_and_failure_analysis(tmp_path):
    from nutrition_eval.report import summarize_runs, write_run_artifacts

    results = sample_results()
    episodes = [item.episode for item in results]
    suite = SuiteResult("complete", episodes)
    summary = summarize_runs(results)
    metadata = {
        "model_id": "gpt-6-luna",
        "tool_version": "v1.0",
        "task_version": "nutrition-eval-50-v1",
        "fixture_version": "synthetic-catalog-v1",
    }

    write_run_artifacts(tmp_path, suite, results, summary, metadata=metadata)

    rows = [json.loads(line) for line in (tmp_path / "episodes.jsonl").read_text().splitlines()]
    assert len(rows) == len(episodes)
    assert rows[0]["task_id"] == "T01"
    assert rows[0]["controller"] == "agent"
    assert rows[0]["repeat"] == 1
    assert rows[0]["metadata"]["model_id"] == "gpt-6-luna"
    assert rows[0]["metadata"]["tool_version"] == "v1.0"
    assert rows[0]["metadata"]["fixture_version"] == "synthetic-catalog-v1"
    assert rows[4]["grade"]["passed"] is False
    assert rows[4]["trace"]

    status = json.loads((tmp_path / "status.json").read_text())
    assert status["status"] == "complete"
    assert status["metadata"] == metadata
    assert "pass@3" in (tmp_path / "summary.md").read_text()
    assert "T02" in (tmp_path / "failure_trace.md").read_text()
    assert "T02" in (tmp_path / "failure_analysis.md").read_text()


def test_incomplete_report_keeps_partial_episodes_without_final_metrics(tmp_path):
    from nutrition_eval.report import write_run_artifacts

    first = scored("T01", "agent", 1, True, 100, 1)
    suite = SuiteResult("incomplete", [first.episode], "judge service unavailable")

    write_run_artifacts(tmp_path, suite, [first], None, metadata={"run_mode": "formal"})

    status = json.loads((tmp_path / "status.json").read_text())
    assert status["status"] == "incomplete"
    assert status["error"] == "judge service unavailable"
    assert len((tmp_path / "episodes.jsonl").read_text().splitlines()) == 1
    assert not (tmp_path / "summary.md").exists()
    assert not (tmp_path / "failure_analysis.md").exists()


def test_cli_aborts_before_execution_on_invalid_taskset_or_unsafe_database(tmp_path, monkeypatch):
    from nutrition_eval import __main__ as cli

    factory_calls = []
    monkeypatch.setattr(cli, "agent_factory", lambda *_args, **_kwargs: factory_calls.append("agent"))
    monkeypatch.setattr(cli, "baseline_factory", lambda *_args, **_kwargs: factory_calls.append("baseline"))
    monkeypatch.setenv("TEST_DATABASE_URL", "host=db_test dbname=nutrition_test user=test password=test")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    invalid = tmp_path / "invalid.jsonl"
    invalid.write_text("not json\n")
    result = cli.main([
        "--tasks", str(invalid),
        "--config", str(Path(__file__).resolve().parents[1] / "eval_config.json"),
        "--output", str(tmp_path / "invalid-run"),
    ])
    assert result == 2
    assert factory_calls == []

    monkeypatch.setenv("TEST_DATABASE_URL", "host=db dbname=nutrition user=test password=test")
    result = cli.main([
        "--tasks", str(Path(__file__).resolve().parents[1] / "tasks.jsonl"),
        "--config", str(Path(__file__).resolve().parents[1] / "eval_config.json"),
        "--output", str(tmp_path / "unsafe-run"),
    ])
    assert result == 2
    assert factory_calls == []


def test_fake_client_development_dry_run_is_marked_not_live(tmp_path):
    from nutrition_eval import __main__ as cli

    result = cli.main([
        "--tasks", str(Path(__file__).resolve().parents[1] / "development_tasks.jsonl"),
        "--config", str(Path(__file__).resolve().parents[1] / "eval_config.json"),
        "--output", str(tmp_path / "dry-run"),
        "--dry-run",
    ])

    assert result == 0
    status = json.loads((tmp_path / "dry-run" / "status.json").read_text())
    assert status["run_mode"] == "dry_run"
    assert "not a live model comparison" in (tmp_path / "dry-run" / "summary.md").read_text()


def test_run_artifacts_capture_full_reproducibility_metadata(tmp_path, monkeypatch):
    from hashlib import sha256

    from nutrition_eval import __main__ as cli

    root = Path(__file__).resolve().parents[1]
    config_path = root / "eval_config.json"
    monkeypatch.setenv("EVAL_PROGRAM_COMMIT", "review-test-commit")
    result = cli.main([
        "--tasks", str(root / "development_tasks.jsonl"),
        "--config", str(config_path),
        "--output", str(tmp_path / "reproducible-run"),
        "--dry-run",
    ])

    assert result == 0
    status = json.loads((tmp_path / "reproducible-run" / "status.json").read_text())
    metadata = status["metadata"]
    config = json.loads(config_path.read_text())
    assert metadata["program_commit"] == "review-test-commit"
    assert len(metadata["source_tree_sha256"]) == 64
    assert metadata["eval_config_sha256"] == sha256(config_path.read_bytes()).hexdigest()
    assert metadata["frozen_eval_config"] == config
    assert metadata["controller_limits"] == {
        "max_model_calls": 12,
        "max_tool_calls": 24,
        "max_clarifications": 3,
        "max_output_tokens": 4096,
        "timeout_seconds": 45,
    }
    assert metadata["database_migrations"] == [{
        "version": config["database_migration_version"],
        "sha256": config["database_migration_sha256"],
    }]
    assert metadata["judge_parameters"] == config["judge_parameters"]
    assert metadata["judge_instructions"] == cli.JUDGE_INSTRUCTIONS
    assert metadata["judge_schema"] == cli.JUDGE_SCHEMA
    assert metadata["judge_instructions_sha256"] == config["judge_instructions_sha256"]
    assert metadata["judge_schema_sha256"] == config["judge_schema_sha256"]


def test_formal_cli_requires_program_commit_before_controllers(tmp_path, monkeypatch):
    from argparse import Namespace

    import pytest

    from nutrition_eval import __main__ as cli

    root = Path(__file__).resolve().parents[1]
    factory_calls = []
    monkeypatch.setattr(cli, "agent_factory", lambda *_args, **_kwargs: factory_calls.append("agent"))
    monkeypatch.setattr(cli, "baseline_factory", lambda *_args, **_kwargs: factory_calls.append("baseline"))
    monkeypatch.setenv("TEST_DATABASE_URL", "host=db_test dbname=nutrition_test user=test password=test")
    monkeypatch.setenv("OPENAI_API_KEY", "test-placeholder")
    monkeypatch.delenv("EVAL_PROGRAM_COMMIT", raising=False)

    monkeypatch.setattr(cli, "_validate_test_database", lambda: {"host": "db_test", "dbname": "nutrition_test"})
    args = Namespace(
        tasks=root / "tasks.jsonl",
        config=root / "eval_config.json",
        output=tmp_path / "formal-run",
        dry_run=False,
    )
    with pytest.raises(ValueError, match="EVAL_PROGRAM_COMMIT"):
        cli._preflight(args)
    assert factory_calls == []
