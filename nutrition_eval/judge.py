"""Frozen structured rubric judge; it never participates in controller decisions."""
import json
import jsonschema
import time

from .contracts import GradePart


JUDGE_VERSION = "nutrition-reply-judge-v2"
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


def grade_reply(task, episode, *, judge_client, judge_config) -> GradePart:
    if not episode.reply:
        return GradePart(False, ["controller produced no user-facing reply"])
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
