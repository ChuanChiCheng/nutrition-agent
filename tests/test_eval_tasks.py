import json

import pytest


def task_record(task_id="T01", *, category="nutrition", labels=None):
    return {
        "id": task_id,
        "type": "unanswerable" if "unanswerable" in (labels or []) else "rubric",
        "question": "Plan a meal.",
        "rubric": ["Do not invent data."],
        "category": category,
        "labels": labels or [],
        "fixture": {"synthetic": True},
        "scripted_answers": [],
        "approval": None,
        "expected_changes": [],
        "required_order": [],
    }


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


@pytest.mark.parametrize(
    "content",
    [
        '{"id":\n',
        "\n".join(json.dumps(task_record()) for _ in range(2)) + "\n",
        json.dumps({key: value for key, value in task_record().items() if key != "question"}) + "\n",
    ],
    ids=["invalid-json", "duplicate-id", "missing-field"],
)
def test_load_tasks_rejects_invalid_json_duplicate_ids_and_missing_fields(tmp_path, content):
    from nutrition_eval.tasks import load_tasks

    path = tmp_path / "tasks.jsonl"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match=r"line 1|line 2|T01"):
        load_tasks(path)


def test_load_tasks_preserves_decimal_values_and_rejects_non_finite_values(tmp_path):
    from decimal import Decimal

    from nutrition_eval.tasks import load_tasks

    path = tmp_path / "tasks.jsonl"
    row = task_record()
    row["fixture"]["quantity"] = 0.125
    write_jsonl(path, [row])

    loaded = load_tasks(path)
    assert loaded[0].fixture["quantity"] == Decimal("0.125")

    path.write_text(json.dumps(row).replace("0.125", "NaN") + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"line 1.*non-finite|non-finite.*line 1"):
        load_tasks(path)


def test_load_tasks_rejects_unknown_label_and_invalid_approval(tmp_path):
    from nutrition_eval.tasks import load_tasks

    path = tmp_path / "tasks.jsonl"
    row = task_record(labels=["urgent"])
    write_jsonl(path, [row])
    with pytest.raises(ValueError, match=r"T01.*line 1|line 1.*T01"):
        load_tasks(path)

    row["labels"] = []
    row["approval"] = "maybe"
    write_jsonl(path, [row])
    with pytest.raises(ValueError, match=r"T01.*line 1|line 1.*T01"):
        load_tasks(path)


def test_expected_change_requires_semantic_match_and_parses_into_contract(tmp_path):
    from nutrition_eval.contracts import ExpectedChange
    from nutrition_eval.tasks import load_tasks

    path = tmp_path / "tasks.jsonl"
    row = task_record()
    row["type"] = "tool"
    row["expected_changes"] = [
        {
            "op": "insert",
            "entity": "events",
            "match": {"batch_id": "batch-1", "eaten_on": "2026-11-18"},
            "values": {"boxes": 1},
        }
    ]
    write_jsonl(path, [row])

    loaded = load_tasks(path)
    assert loaded[0].expected_changes == [
        ExpectedChange(
            op="insert",
            entity="events",
            match={"batch_id": "batch-1", "eaten_on": "2026-11-18"},
            values={"boxes": 1},
        )
    ]

    row["expected_changes"][0]["match"] = {}
    write_jsonl(path, [row])
    with pytest.raises(ValueError, match=r"semantic match"):
        load_tasks(path)


def formal_tasks(*, edge_count=3, unanswerable_count=2, count=50):
    from nutrition_eval.contracts import EvalTask

    tasks = []
    for index in range(count):
        labels = set()
        if index < edge_count:
            labels.add("edge")
        if index < unanswerable_count:
            labels.add("unanswerable")
        tasks.append(
            EvalTask(
                id=f"T{index + 1:02d}",
                category="unanswerable" if "unanswerable" in labels else "nutrition",
                labels=labels,
                fixture={"synthetic": True},
                request="Plan a meal.",
                scripted_answers=[],
                approval=None,
                expected_changes=[],
                required_order=[],
                reply_rubric=["Do not invent data."],
            )
        )
    return tasks


def test_formal_taskset_requires_50_three_edges_two_unanswerables():
    from nutrition_eval.tasks import validate_taskset

    valid = formal_tasks()
    validate_taskset(valid)

    with pytest.raises(ValueError, match="50"):
        validate_taskset(formal_tasks(count=49))

    duplicate = formal_tasks()
    duplicate[-1] = duplicate[0]
    with pytest.raises(ValueError, match="duplicate"):
        validate_taskset(duplicate)

    with pytest.raises(ValueError, match="edge"):
        validate_taskset(formal_tasks(edge_count=2))

    with pytest.raises(ValueError, match="unanswerable"):
        validate_taskset(formal_tasks(unanswerable_count=1))


def test_unanswerable_task_cannot_include_scripted_answer_or_expected_change(tmp_path):
    from nutrition_eval.tasks import load_tasks

    path = tmp_path / "tasks.jsonl"
    row = task_record(category="unanswerable", labels=["unanswerable"])
    row["scripted_answers"] = ["It was chicken curry."]
    write_jsonl(path, [row])

    with pytest.raises(ValueError, match=r"unanswerable.*scripted|scripted.*unanswerable"):
        load_tasks(path)



def test_load_tasks_reads_lecture_slide_fields(tmp_path):
    from nutrition_eval.tasks import load_tasks

    path = tmp_path / "tasks.jsonl"
    write_jsonl(path, [task_record()])

    task = load_tasks(path)[0]
    assert task.task_type == "rubric"
    assert task.request == "Plan a meal."
    assert task.reply_rubric == ["Do not invent data."]


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"type": "exact"}, r"type"),
        ({"type": "tool"}, r"'tool' requires"),
        ({"type": "rubric", "required_order": [{"event": "write"}]}, r"use 'tool'"),
        ({"type": "unanswerable"}, r"'unanswerable' label"),
        ({"type": "rubric", "labels": ["unanswerable"], "category": "unanswerable"}, r"'unanswerable' label"),
    ],
    ids=["unsupported-type", "tool-without-actions", "rubric-with-actions", "type-without-label", "label-without-type"],
)
def test_task_type_must_match_grading_shape(tmp_path, changes, message):
    from nutrition_eval.tasks import load_tasks

    path = tmp_path / "tasks.jsonl"
    row = task_record()
    row.update(changes)
    write_jsonl(path, [row])

    with pytest.raises(ValueError, match=message):
        load_tasks(path)
