"""Run one scripted conversation and capture process, trace, state and metrics."""
from copy import deepcopy
import time

from .contracts import EpisodeResult, EvalTask
from .state import normalize_state, read_business_state


def _data(result) -> dict:
    value = getattr(result, "data", {})
    return value if isinstance(value, dict) else {}


def _trace_for(result, store) -> list[dict]:
    data = _data(result)
    trace = data.get("trace")
    if isinstance(trace, list):
        return deepcopy(trace)

    run_id = data.get("run_id")
    if run_id:
        try:
            with store.transaction() as connection:
                row = connection.execute("SELECT trace FROM agent_runs WHERE id=%s", (run_id,)).fetchone()
            if row and isinstance(row.get("trace"), list):
                return deepcopy(row["trace"])
        except Exception:
            pass

    rows = data.get("tool_results", [])
    return [
        {"type": "tool", **deepcopy(row)}
        for row in rows
        if isinstance(row, dict)
    ]


def _explicit_ask_user(result) -> dict | None:
    data = _data(result)
    if data.get("action") == "ask_user" and getattr(result, "ok", False):
        return {"name": "ask_user", "arguments": data.get("arguments", {})}
    for row in data.get("tool_results", []):
        if isinstance(row, dict) and row.get("name") == "ask_user":
            operation = row.get("result")
            if isinstance(operation, dict) and operation.get("ok") is False:
                continue
            return deepcopy(row)
    for row in data.get("trace", []):
        if isinstance(row, dict) and row.get("type") in {"tool", "action"} and row.get("name") == "ask_user":
            operation = row.get("result")
            if isinstance(operation, dict) and operation.get("ok") is False:
                continue
            return deepcopy(row)
    return None


def _visible_preview_id(result) -> str | None:
    data = _data(result)
    preview_id = data.get("pending_preview")
    reply = _reply(result) or ""
    if isinstance(preview_id, str) and preview_id and preview_id in reply:
        return preview_id
    operation = data.get("operation")
    if isinstance(operation, dict):
        operation_data = operation.get("data", {})
        if isinstance(operation_data, dict) and isinstance(operation_data.get("id"), str) and operation_data["id"] in reply:
            return operation_data["id"]
    for row in data.get("tool_results", []):
        if not isinstance(row, dict) or not str(row.get("name", "")).startswith("preview_"):
            continue
        operation = row.get("result", {})
        if isinstance(operation, dict):
            operation_data = operation.get("data", {})
            if isinstance(operation_data, dict) and isinstance(operation_data.get("id"), str) and operation_data["id"] in reply:
                return operation_data["id"]
    return None


def _reply(result) -> str | None:
    data = _data(result)
    for key in ("message", "reply"):
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
    error = getattr(result, "error", None)
    return error if isinstance(error, str) and error else None


def _usage(trace: list[dict]) -> tuple[int, int]:
    input_tokens = output_tokens = 0
    for row in trace:
        if not isinstance(row, dict) or row.get("type") != "model":
            continue
        usage = row.get("usage") or {}
        if not isinstance(usage, dict):
            continue
        input_tokens += int(usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0)
        output_tokens += int(usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0)
    return input_tokens, output_tokens


def _counts(result, trace: list[dict]) -> tuple[int, int]:
    counts = _data(result).get("counts", {})
    if not isinstance(counts, dict):
        counts = {}
    model_calls = counts.get("model_calls")
    tool_calls = counts.get("tool_calls")
    if model_calls is None:
        model_calls = sum(row.get("type") == "model" for row in trace if isinstance(row, dict))
    if tool_calls is None:
        tool_calls = sum(row.get("type") in {"tool", "action"} for row in trace if isinstance(row, dict))
    return int(model_calls), int(tool_calls)


def _limit_error(result, *, model_calls, tool_calls, latency_seconds, limits) -> str | None:
    if _data(result).get("limit_reached"):
        return "controller resource limit reached"
    if model_calls > limits.get("max_model_calls", float("inf")):
        return "model call limit exceeded"
    if tool_calls > limits.get("max_tool_calls", float("inf")):
        return "tool call limit exceeded"
    if latency_seconds > limits.get("timeout_seconds", float("inf")):
        return "episode timeout exceeded"
    return None


def run_episode(
    task: EvalTask,
    controller,
    store,
    *,
    repeat: int,
    now,
    limits: dict,
) -> EpisodeResult:
    trace: list[dict] = []
    interactions: list[dict] = [
        {
            "kind": "episode_start",
            "repeat": repeat,
            "now": now.isoformat() if hasattr(now, "isoformat") else str(now),
        }
    ]
    total_model_calls = total_tool_calls = input_tokens = output_tokens = turns = 0
    latency_seconds = 0.0
    latest_reply = None
    error = None
    clarification_count = 0
    answer_index = 0
    approval_used = False
    last_preview_id = None
    current_message = task.request
    current_kind = "request"

    def record(result, *, interaction_kind):
        nonlocal total_model_calls, total_tool_calls, input_tokens, output_tokens, turns, latest_reply
        turns += 1
        result_trace = _trace_for(result, store)
        trace.extend(result_trace)
        model_count, tool_count = _counts(result, result_trace)
        total_model_calls += model_count
        total_tool_calls += tool_count
        in_count, out_count = _usage(result_trace)
        input_tokens += in_count
        output_tokens += out_count
        latest_reply = _reply(result)
        interactions.append(
            {
                "kind": interaction_kind,
                "turn": turns,
                "reply": latest_reply,
                "ok": bool(getattr(result, "ok", False)),
            }
        )
        return result_trace

    while current_message is not None:
        if turns and total_model_calls >= limits.get("max_model_calls", float("inf")):
            error = "model call limit reached before the next scripted message"
            break
        if turns and total_tool_calls >= limits.get("max_tool_calls", float("inf")):
            error = "tool call limit reached before the next scripted message"
            break
        interactions.append({"kind": current_kind, "message": current_message})
        call_started = time.monotonic()
        try:
            result = controller.handle(current_message)
        except Exception as exc:
            latency_seconds += max(0.0, time.monotonic() - call_started)
            error = f"controller {type(exc).__name__}: {exc}"
            trace.append({"type": "controller_error", "class": type(exc).__name__})
            break
        latency_seconds += max(0.0, time.monotonic() - call_started)
        result_trace = record(result, interaction_kind="reply")
        if not getattr(result, "ok", False):
            error = getattr(result, "error", None) or "controller returned an unsuccessful result"
            break

        error = _limit_error(
            result,
            model_calls=total_model_calls,
            tool_calls=total_tool_calls,
            latency_seconds=latency_seconds,
            limits=limits,
        )
        if error:
            break

        ask = _explicit_ask_user(result)
        if ask:
            clarification_count += 1
            interactions.append(
                {
                    "kind": "ask_user",
                    "topic": ask.get("arguments", {}).get("topic"),
                    "question": _reply(result),
                    "turn": turns,
                }
            )
            if clarification_count > limits.get("max_clarifications", float("inf")):
                error = "clarification limit exceeded"
                break

        preview_id = _visible_preview_id(result)
        if preview_id and preview_id != last_preview_id:
            last_preview_id = preview_id
            interactions.append({"kind": "preview", "preview_id": preview_id, "turn": turns})
            if task.approval and not approval_used:
                approval_used = True
                interactions.append(
                    {"kind": "approval", "preview_id": preview_id, "outcome": task.approval}
                )
                approval_started = time.monotonic()
                try:
                    approval_result = controller.approve(preview_id, task.approval)
                except Exception as exc:
                    latency_seconds += max(0.0, time.monotonic() - approval_started)
                    error = f"approval {type(exc).__name__}: {exc}"
                    trace.append({"type": "approval_error", "preview_id": preview_id, "class": type(exc).__name__})
                    break
                latency_seconds += max(0.0, time.monotonic() - approval_started)
                record(approval_result, interaction_kind="approval_result")
                if not getattr(approval_result, "ok", False):
                    error = getattr(approval_result, "error", None) or "approval did not match the displayed preview"
                    interactions.append({"kind": "process_error", "error": error})
                    break
                error = _limit_error(
                    approval_result,
                    model_calls=total_model_calls,
                    tool_calls=total_tool_calls,
                    latency_seconds=latency_seconds,
                    limits=limits,
                )
                if error:
                    break

        if ask and answer_index < len(task.scripted_answers):
            current_message = task.scripted_answers[answer_index]
            answer_index += 1
            current_kind = "scripted_answer"
        else:
            current_message = None

    try:
        final_state = normalize_state(read_business_state(store))
    except Exception as exc:
        final_state = {}
        if error is None:
            error = f"final state read {type(exc).__name__}: {exc}"

    return EpisodeResult(
        task_id=task.id,
        controller=getattr(controller, "name", controller.__class__.__name__),
        repeat=repeat,
        status="failed" if error else "complete",
        reply=latest_reply,
        trace=trace,
        interactions=interactions,
        final_state=final_state,
        turns=turns,
        model_calls=total_model_calls,
        tool_calls=total_tool_calls,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=round(latency_seconds * 1000),
        error=error,
    )
