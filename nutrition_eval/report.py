"""Evaluation metrics and durable run artifacts."""
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
import json
import math
from pathlib import Path
from statistics import mean


def _jsonable(value):
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(child) for key, child in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(child) for child in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _nearest_rank_p95(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = math.ceil(0.95 * len(ordered))
    return ordered[rank - 1]


def _component_counts(rows: list) -> dict:
    counts = {}
    for name in ("state", "order", "reply"):
        passed = sum(bool(getattr(row.grade, name).passed) for row in rows)
        counts[name] = {
            "sample_count": len(rows),
            "passed_count": passed,
            "failed_count": len(rows) - passed,
        }
    return counts


def _controller_metrics(rows: list) -> dict:
    if not rows:
        return {
            "sample_count": 0,
            "passed_count": 0,
            "accuracy": None,
            "mean_turns": None,
            "mean_model_calls": None,
            "mean_tool_calls": None,
            "mean_latency_ms": None,
            "p95_latency_ms": None,
            "mean_tokens": None,
            "components": _component_counts(rows),
        }
    episodes = [row.episode for row in rows]
    passed = sum(bool(row.grade.passed) for row in rows)
    latencies = [episode.latency_ms for episode in episodes]
    return {
        "sample_count": len(rows),
        "passed_count": passed,
        "accuracy": passed / len(rows),
        "mean_turns": mean(episode.turns for episode in episodes),
        "mean_model_calls": mean(episode.model_calls for episode in episodes),
        "mean_tool_calls": mean(episode.tool_calls for episode in episodes),
        "mean_latency_ms": mean(latencies),
        "p95_latency_ms": _nearest_rank_p95(latencies),
        "mean_tokens": mean(episode.input_tokens + episode.output_tokens for episode in episodes),
        "components": _component_counts(rows),
    }


def summarize_runs(results: list) -> dict:
    """Summarize complete scored episodes; p95 uses nearest rank over episodes."""
    controllers = {
        name: _controller_metrics([row for row in results if row.episode.controller == name])
        for name in sorted({row.episode.controller for row in results} | {"agent", "baseline"})
    }
    by_category: dict[str, dict[str, list]] = {}
    for row in results:
        by_category.setdefault(row.episode.controller, {}).setdefault(row.task.category, []).append(row)
    category_metrics = {
        controller: {
            category: {
                "sample_count": len(rows),
                "passed_count": sum(bool(row.grade.passed) for row in rows),
                "components": _component_counts(rows),
            }
            for category, rows in sorted(categories.items())
        }
        for controller, categories in sorted(by_category.items())
    }
    agent_rows = [row for row in results if row.episode.controller == "agent"]
    by_task: dict[str, list] = {}
    for row in agent_rows:
        by_task.setdefault(row.episode.task_id, []).append(row)
    for rows in by_task.values():
        rows.sort(key=lambda row: row.episode.repeat)

    repeated = {task_id: rows for task_id, rows in by_task.items() if len(rows) == 3}
    repeat_ids = sorted({row.episode.repeat for row in agent_rows})
    accuracy_by_repeat = {}
    for repeat in repeat_ids:
        sample = [row for row in agent_rows if row.episode.repeat == repeat]
        accuracy_by_repeat[repeat] = (
            sum(bool(row.grade.passed) for row in sample) / len(sample) if sample else None
        )
    any_pass = sum(any(row.grade.passed for row in rows) for rows in repeated.values())
    all_pass = sum(all(row.grade.passed for row in rows) for rows in repeated.values())
    flipped = sorted(
        task_id
        for task_id, rows in repeated.items()
        if len({bool(row.grade.passed) for row in rows}) > 1
    )
    denominator = len(repeated)
    agent_summary = {
        "pass_at_3": any_pass / denominator if denominator else None,
        "pass_power_3": all_pass / denominator if denominator else None,
        "repeated_task_count": denominator,
        "flipped_task_ids": flipped,
        "accuracy_by_repeat": accuracy_by_repeat,
    }
    return {"controllers": controllers, "by_category": category_metrics, "agent": agent_summary}


def _failure_reasons(scored) -> list[str]:
    if scored is None:
        return []
    parts = []
    for name in ("state", "order", "reply"):
        part = getattr(scored.grade, name)
        if not part.passed:
            parts.extend(f"{name}: {reason}" for reason in part.reasons)
    if scored.episode.status != "complete":
        parts.append(f"episode: {scored.episode.error or scored.episode.status}")
    return parts


def _summary_markdown(summary: dict, metadata: dict) -> str:
    lines = ["# Evaluation Summary", ""]
    mode = metadata.get("run_mode", "formal")
    lines.extend([f"Run mode: `{mode}`", ""])
    if mode == "dry_run":
        lines.extend(["This is a deterministic fake-client dry run; it is not a live model comparison.", ""])
    lines.extend([
        "| Controller | Episodes | Accuracy | Mean turns | Mean model calls | Mean latency (ms) | p95 latency (ms, nearest rank) | Mean tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for name in ("agent", "baseline"):
        item = summary["controllers"].get(name, {})
        accuracy = "—" if item.get("accuracy") is None else f"{item['accuracy'] * 100:.1f}% ({item['passed_count']}/{item['sample_count']})"
        mean_turns = "—" if item.get("mean_turns") is None else f"{item['mean_turns']:.2f}"
        mean_calls = "—" if item.get("mean_model_calls") is None else f"{item['mean_model_calls']:.2f}"
        mean_latency = "—" if item.get("mean_latency_ms") is None else f"{item['mean_latency_ms']:.1f}"
        p95 = "—" if item.get("p95_latency_ms") is None else str(item["p95_latency_ms"])
        mean_tokens = "—" if item.get("mean_tokens") is None else f"{item['mean_tokens']:.1f}"
        lines.append(f"| {name} | {item.get('sample_count', 0)} | {accuracy} | {mean_turns} | {mean_calls} | {mean_latency} | {p95} | {mean_tokens} |")

    lines.extend([
        "",
        "## Component outcomes",
        "",
        "Counts are passed episodes / attempts. Component counts can overlap; overall success requires state, order, and response to pass.",
        "",
        "| Controller | Category | Overall | State | Order | Response |",
        "|---|---|---:|---:|---:|---:|",
    ])

    def count_text(counts):
        return f"{counts['passed_count']}/{counts['sample_count']}"

    for controller in ("agent", "baseline"):
        for category, values in summary.get("by_category", {}).get(controller, {}).items():
            lines.append(
                f"| {controller} | {category} | {values['passed_count']}/{values['sample_count']} | "
                f"{count_text(values['components']['state'])} | "
                f"{count_text(values['components']['order'])} | "
                f"{count_text(values['components']['reply'])} |"
            )

    agent = summary["agent"]
    lines.extend(["", "## Agent repeat metrics", ""])
    for repeat, accuracy in sorted(agent["accuracy_by_repeat"].items()):
        lines.append(f"- Repeat {repeat} accuracy: {accuracy * 100:.1f}%.")
    pass_at_3 = "—" if agent["pass_at_3"] is None else f"{agent['pass_at_3'] * 100:.1f}%"
    pass_power_3 = "—" if agent["pass_power_3"] is None else f"{agent['pass_power_3'] * 100:.1f}%"
    lines.extend([
        f"- pass@3: {pass_at_3} across {agent['repeated_task_count']} tasks.",
        f"- pass^3: {pass_power_3} across {agent['repeated_task_count']} tasks.",
        f"- Flipped task IDs: {', '.join(agent['flipped_task_ids']) if agent['flipped_task_ids'] else 'none'}.",
        "",
    ])
    return "\n".join(lines)


def _failure_documents(suite, results) -> tuple[str, str]:
    scored_by_key = {
        (row.episode.task_id, row.episode.controller, row.episode.repeat): row
        for row in results
    }
    failures = []
    for episode in suite.episodes:
        scored = scored_by_key.get((episode.task_id, episode.controller, episode.repeat))
        if episode.status != "complete" or (scored is not None and not scored.grade.passed):
            failures.append((episode, scored))
    if not failures:
        no_failure = "No controller failure was observed in this complete run.\n"
        return no_failure, no_failure

    episode, scored = failures[0]
    reasons = _failure_reasons(scored)
    if scored is None:
        component_outcomes = "Component outcomes unavailable because this episode has no score."
    else:
        component_outcomes = "Component outcomes: " + ", ".join(
            f"{label} {'PASS' if getattr(scored.grade, name).passed else 'FAIL'}"
            for name, label in (("state", "state"), ("order", "order"), ("reply", "response"))
        ) + "."
    if episode.error and not any(reason.startswith("episode:") for reason in reasons):
        reasons.append(f"episode: {episode.error}")
    trace_json = json.dumps(_jsonable(episode.trace), ensure_ascii=False, indent=2, sort_keys=True)
    trace_doc = "\n".join([
        "# Failure Trace",
        "",
        f"Task `{episode.task_id}`, controller `{episode.controller}`, repeat {episode.repeat}.",
        "",
        component_outcomes,
        "",
        "Observed grading findings:",
        *[f"- {reason}" for reason in reasons],
        "",
        "```json",
        trace_json,
        "```",
        "",
    ])
    actions = [
        str(row.get("name"))
        for row in episode.trace
        if isinstance(row, dict) and row.get("type") in {"tool", "action"} and row.get("name")
    ]
    observation = ", ".join(actions) if actions else "no tool/action call was recorded"
    reason_text = "; ".join(reasons) if reasons else "the episode ended before a complete grade was available"
    analysis = (
        f"Task {episode.task_id} failed for {episode.controller} repeat {episode.repeat}. "
        f"The preserved trace records {observation}. {component_outcomes} The observed grader findings were: {reason_text}. "
        "This identifies the failing step and state or response consequence from recorded evidence; "
        "review the first failing action and its service result before changing the controller."
    )
    return trace_doc, "# Failure Analysis\n\n" + analysis + "\n"


def write_run_artifacts(
    output_dir: Path,
    suite,
    results: list,
    summary: dict | None,
    *,
    metadata: dict | None = None,
) -> None:
    """Persist complete or partial samples without promoting incomplete metrics."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata = dict(metadata or {})
    scored_by_key = {
        (row.episode.task_id, row.episode.controller, row.episode.repeat): row
        for row in results
    }
    records = []
    for episode in suite.episodes:
        key = (episode.task_id, episode.controller, episode.repeat)
        scored = scored_by_key.get(key)
        model_ids = sorted({
            row.get("model") or row.get("requested_model")
            for row in episode.trace
            if isinstance(row, dict) and row.get("type") == "model"
        } - {None})
        record = {
            "task_id": episode.task_id,
            "controller": episode.controller,
            "repeat": episode.repeat,
            "status": episode.status,
            "reply": episode.reply,
            "trace": episode.trace,
            "interactions": episode.interactions,
            "final_state": episode.final_state,
            "metrics": {
                "turns": episode.turns,
                "model_calls": episode.model_calls,
                "tool_calls": episode.tool_calls,
                "input_tokens": episode.input_tokens,
                "output_tokens": episode.output_tokens,
                "latency_ms": episode.latency_ms,
            },
            "error": episode.error,
            "grade": scored.grade if scored is not None else None,
            "metadata": {**metadata, "observed_model_ids": model_ids},
        }
        records.append(_jsonable(record))
    (output_dir / "episodes.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in records),
        encoding="utf-8",
    )

    complete = suite.status == "complete" and summary is not None
    status = {
        "status": "complete" if complete else "incomplete",
        "run_mode": metadata.get("run_mode", "formal"),
        "error": suite.error,
        "episode_count": len(suite.episodes),
        "scored_episode_count": len(results),
        "metadata": _jsonable(metadata),
    }
    (output_dir / "status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if not complete:
        for name in ("summary.md", "failure_analysis.md"):
            (output_dir / name).unlink(missing_ok=True)
    else:
        (output_dir / "summary.md").write_text(_summary_markdown(summary, metadata), encoding="utf-8")
        trace_doc, analysis_doc = _failure_documents(suite, results)
        (output_dir / "failure_trace.md").write_text(trace_doc, encoding="utf-8")
        (output_dir / "failure_analysis.md").write_text(analysis_doc, encoding="utf-8")
