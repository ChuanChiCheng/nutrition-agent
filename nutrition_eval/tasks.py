import json
from decimal import Decimal
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

from .contracts import EvalTask, ExpectedChange


CATEGORIES = {
    "nutrition",
    "preparation",
    "addons",
    "meal_logging",
    "corrections",
    "queries",
    "unanswerable",
}
LABELS = {"edge", "unanswerable"}

_CHANGE_SCHEMA = {
    "type": "object",
    "required": ["op", "entity", "match", "values"],
    "additionalProperties": False,
    "properties": {
        "op": {"enum": ["insert", "update", "delete"]},
        "entity": {"type": "string", "minLength": 1},
        "match": {"type": "object"},
        "values": {"type": "object"},
    },
}

TASK_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "id",
        "category",
        "labels",
        "fixture",
        "request",
        "scripted_answers",
        "approval",
        "expected_changes",
        "required_order",
        "reply_rubric",
    ],
    "additionalProperties": False,
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "category": {"enum": sorted(CATEGORIES)},
        "labels": {
            "type": "array",
            "items": {"enum": sorted(LABELS)},
            "uniqueItems": True,
        },
        "fixture": {"type": "object"},
        "request": {"type": "string", "minLength": 1},
        "scripted_answers": {"type": "array", "items": {"type": "string"}},
        "approval": {"enum": ["approve", "reject", None]},
        "expected_changes": {
            "type": "array",
            "items": _CHANGE_SCHEMA,
        },
        "required_order": {"type": "array", "items": {"type": "object"}},
        "reply_rubric": {
            "type": "array",
            "minItems": 1,
            "items": {"type": "string", "minLength": 1},
        },
    },
}
_VALIDATOR = Draft202012Validator(TASK_SCHEMA)


def _reject_non_finite(value: str):
    raise ValueError(f"non-finite numeric value {value}")


def _location(path: Path, line_number: int, task_id: object = None) -> str:
    task_part = f" task {task_id!r}" if isinstance(task_id, str) else ""
    return f"{path}: line {line_number}{task_part}"


def _to_task(record: dict) -> EvalTask:
    if "unanswerable" in record["labels"] and (
        record["scripted_answers"] or record["expected_changes"] or record["approval"]
    ):
        raise ValueError(
            "unanswerable tasks cannot have scripted answers, expected changes, or approvals"
        )
    changes = []
    for change in record["expected_changes"]:
        if not change["match"] or "id" in change["match"]:
            raise ValueError(
                "expected changes require semantic match fields and cannot match on generated id"
            )
        if change["op"] in {"insert", "update"} and not change["values"]:
            raise ValueError(f"{change['op']} expected changes require values")
        if change["op"] == "delete" and change["values"]:
            raise ValueError("delete expected changes must have empty values")
        if "id" in change["values"]:
            raise ValueError("expected change values cannot prescribe generated ids")
        changes.append(ExpectedChange(**change))
    return EvalTask(
        id=record["id"],
        category=record["category"],
        labels=set(record["labels"]),
        fixture=record["fixture"],
        request=record["request"],
        scripted_answers=record["scripted_answers"],
        approval=record["approval"],
        expected_changes=changes,
        required_order=record["required_order"],
        reply_rubric=record["reply_rubric"],
    )


def load_tasks(path: Path, *, expected_count: int | None = None) -> list[EvalTask]:
    """Load and validate one UTF-8 JSONL task file with line-specific errors."""
    tasks = []
    seen: dict[str, int] = {}

    try:
        stream = path.open("r", encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"cannot read task file {path}: {exc}") from exc

    with stream:
        for line_number, raw_line in enumerate(stream, start=1):
            if not raw_line.strip():
                raise ValueError(f"{path}: line {line_number}: blank lines are not valid JSONL tasks")
            try:
                record = json.loads(
                    raw_line,
                    parse_float=Decimal,
                    parse_constant=_reject_non_finite,
                )
            except (json.JSONDecodeError, ValueError) as exc:
                raise ValueError(f"{path}: line {line_number}: invalid JSON: {exc}") from exc

            task_id = record.get("id") if isinstance(record, dict) else None
            location = _location(path, line_number, task_id)
            if not isinstance(record, dict):
                raise ValueError(f"{location}: each JSONL row must be an object")

            errors = sorted(_VALIDATOR.iter_errors(record), key=lambda error: list(error.path))
            if errors:
                detail = "; ".join(error.message for error in errors)
                raise ValueError(f"{location}: invalid task: {detail}")

            task_id = record["id"]
            if task_id in seen:
                raise ValueError(
                    f"{location}: duplicate task id; first appeared on line {seen[task_id]}"
                )
            seen[task_id] = line_number

            try:
                task = _to_task(record)
            except ValueError as exc:
                raise ValueError(f"{location}: {exc}") from exc
            tasks.append(task)

    if expected_count is not None and len(tasks) != expected_count:
        raise ValueError(
            f"{path}: expected {expected_count} tasks, found {len(tasks)}"
        )
    return tasks


def validate_taskset(tasks: list[EvalTask], *, expected_count: int = 50) -> None:
    if expected_count < 1:
        raise ValueError("expected_count must be positive")
    if len(tasks) != expected_count:
        raise ValueError(f"expected {expected_count} tasks, found {len(tasks)}")

    ids = [task.id for task in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError("taskset contains duplicate task ids")

    edge_count = sum("edge" in task.labels for task in tasks)
    unanswerable_count = sum("unanswerable" in task.labels for task in tasks)
    if edge_count < 3:
        raise ValueError(f"formal taskset requires at least 3 edge tasks; found {edge_count}")
    if unanswerable_count < 2:
        raise ValueError(
            "formal taskset requires at least 2 unanswerable tasks; "
            f"found {unanswerable_count}"
        )
