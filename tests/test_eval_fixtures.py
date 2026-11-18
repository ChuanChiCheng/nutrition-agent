from copy import deepcopy
from decimal import Decimal
import os

import psycopg
import pytest


def fixture_data():
    source = {"status": "synthetic", "note": "evaluation fixture"}
    addon = {
        "ingredient_id": "yogurt",
        "quantity": "1",
        "unit": "serving",
        "state": "packaged",
        "nutrients": {"kcal": "100", "protein_g": "15", "carbs_g": "8", "fat_g": "1"},
        "source": source,
    }
    batch_data = {
        "box_nutrients": {"kcal": "600", "protein_g": "40", "carbs_g": "65", "fat_g": "20"},
        "box_cost": {"known_subtotal": "2.50", "total": "2.50"},
        "sources": [source],
        "targets": {"kcal": "600", "protein_g": "40", "carbs_g": "65", "fat_g": "20"},
    }
    meal_data = {
        "batch_id": "batch-meal",
        "batch_name": "meal boxes",
        "eaten_on": "2026-11-17",
        "meal": "dinner",
        "box_nutrients": batch_data["box_nutrients"],
        "addon_items": [addon],
        "addon_nutrients": addon["nutrients"],
        "total_nutrients": {"kcal": "700", "protein_g": "55", "carbs_g": "73", "fat_g": "21"},
        "addon_version": 1,
        "box_sources": [source],
    }
    return {
        "synthetic": True,
        "provenance": {"fixture_version": "test-v1"},
        "catalog": {"ingredients": [], "recipes": []},
        "profile": {
            "timezone": "America/Los_Angeles",
            "meal_targets": {"kcal": "600", "protein_g": "40", "carbs_g": "65", "fat_g": "20"},
        },
        "inventory": [
            {"ingredient_id": "chicken", "quantity": "400", "unit": "g", "state": "raw", "source": source},
            {"ingredient_id": "rice", "quantity": "600", "unit": "g", "state": "dry", "source": source},
            {"ingredient_id": "yogurt", "quantity": "1", "unit": "serving", "state": "packaged", "source": source},
        ],
        "cooking_runs": [
            {
                "id": "run-1",
                "recipe_id": "curry",
                "prepared_on": "2026-11-16",
                "request_id": "seed-run-1",
                "data": {"actual_usage": [{"ingredient_id": "chicken", "quantity": "800"}]},
            }
        ],
        "cooking_ingredients": [
            {"id": "ci-chicken", "cooking_run_id": "run-1", "ingredient_id": "chicken", "quantity": "800", "unit": "g", "data": {"source": source}},
            {"id": "ci-rice", "cooking_run_id": "run-1", "ingredient_id": "rice", "quantity": "400", "unit": "g", "data": {"source": source}},
        ],
        "batches": [
            {"id": "batch-meal", "cooking_run_id": "run-1", "name": "meal boxes", "total_boxes": 6, "remaining_boxes": 5, "data": batch_data},
            {"id": "batch-curry", "cooking_run_id": "run-1", "name": "curry only", "total_boxes": 2, "remaining_boxes": 2, "data": batch_data},
        ],
        "batch_ingredients": [
            {"batch_id": "batch-meal", "cooking_ingredient_id": "ci-chicken", "quantity": "600", "unit": "g"},
            {"batch_id": "batch-curry", "cooking_ingredient_id": "ci-chicken", "quantity": "200", "unit": "g"},
            {"batch_id": "batch-meal", "cooking_ingredient_id": "ci-rice", "quantity": "400", "unit": "g"},
        ],
        "batch_addons": [
            {"batch_id": "batch-meal", "version": 1, "items": [addon]},
        ],
        "events": [
            {"id": "event-1", "batch_id": "batch-meal", "eaten_on": "2026-11-17", "meal": "dinner", "boxes": 1, "data": meal_data},
        ],
        "inventory_movements": [
            {"ingredient_id": "chicken", "delta": "1200", "cooking_run_id": None, "event_id": None, "kind": "purchase", "data": {"unit": "g", "snapshot": {"ingredient_id": "chicken", "quantity": "1200", "unit": "g", "source": source}}},
            {"ingredient_id": "chicken", "delta": "-800", "cooking_run_id": "run-1", "event_id": None, "kind": "preparation", "data": {"unit": "g", "snapshot": {"ingredient_id": "chicken", "quantity": "800", "unit": "g", "source": source}}},
            {"ingredient_id": "yogurt", "delta": "-1", "cooking_run_id": None, "event_id": "event-1", "kind": "meal_addon", "data": {"unit": "serving", "snapshot": addon}},
        ],
        "previews": [
            {"id": "preview-1", "kind": "correction", "state_version": 3, "status": "pending", "data": {"payload": {"batch_id": "batch-meal", "event_id": "event-1"}, "changes": [{"event_id": "event-1"}], "summary": "review correction"}, "created_at": "2026-11-18T08:00:00+00:00", "confirmed_at": None},
        ],
        "operations": [
            {"request_id": "seed-operation-1", "input_hash": "same-input", "result": {"event_id": "event-1", "cooking_run_id": "run-1", "batch_ids": ["batch-meal", "batch-curry"]}},
            {"request_id": "seed-operation-2", "input_hash": "same-input", "result": {"event_id": "event-1"}},
        ],
        "workflow_sessions": [
            {"id": "eval-session", "data": {"stage": "preview_confirmation", "pending_preview": "preview-1", "pending_preview_kind": "correction", "proposal": {"id": "proposal-1", "calculation": {"valid": True}}, "accepted_recipe": "proposal-1", "history": []}},
        ],
    }


def db_payload(fixture):
    keys = (
        "profile", "inventory", "cooking_runs", "cooking_ingredients", "batches",
        "batch_ingredients", "batch_addons", "events", "inventory_movements",
        "previews", "operations", "workflow_sessions",
    )
    return {key: fixture.get(key, []) for key in keys}


def schema_exists(dsn, schema_name):
    with psycopg.connect(dsn) as connection:
        return connection.execute(
            "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name=%s)",
            (schema_name,),
        ).fetchone()[0]


def test_fixture_round_trips_all_business_tables():
    from nutrition_eval.fixtures import episode_store, seed_fixture
    from nutrition_eval.state import normalize_state, read_business_state

    dsn = os.environ["TEST_DATABASE_URL"]
    fixture = fixture_data()
    with episode_store(dsn, "eval_roundtrip") as store:
        seed_fixture(store, fixture)
        actual = normalize_state(read_business_state(store))
        expected = normalize_state(db_payload(fixture))

    assert actual == expected
    assert len(actual["batches"]) == 2
    assert len(actual["inventory_movements"]) == 3
    assert len(actual["operations"]) == 2
    assert len(actual["previews"]) == 1
    assert actual["inventory"][0]["quantity"] == "400"


def test_extra_event_or_movement_changes_snapshot():
    from nutrition_demo.store import jsonb
    from nutrition_eval.fixtures import episode_store, seed_fixture
    from nutrition_eval.state import normalize_state, read_business_state

    dsn = os.environ["TEST_DATABASE_URL"]
    with episode_store(dsn, "eval_delta") as store:
        seed_fixture(store, fixture_data())
        baseline = normalize_state(read_business_state(store))
        with store.transaction() as connection:
            connection.execute(
                "INSERT INTO events(id,batch_id,eaten_on,meal,data) VALUES(%s,%s,%s,%s,%s)",
                ("event-extra", "batch-meal", "2026-11-18", "snack", jsonb({"boxes": 1})),
            )
        with store.transaction() as connection:
            connection.execute(
                "INSERT INTO inventory_movements(ingredient_id,delta,kind,data) VALUES(%s,%s,%s,%s)",
                ("chicken", Decimal("-1"), "unexpected", jsonb({"unit": "g"})),
            )
        changed = normalize_state(read_business_state(store))

    assert changed != baseline
    assert len(changed["events"]) == len(baseline["events"]) + 1
    assert len(changed["inventory_movements"]) == len(baseline["inventory_movements"]) + 1


def test_normalization_replaces_generated_ids_and_preserves_duplicate_rows():
    from nutrition_eval.state import normalize_state

    original = db_payload(fixture_data())
    renamed = deepcopy(original)
    replacements = {
        "run-1": "run-new",
        "ci-chicken": "ci-chicken-new",
        "ci-rice": "ci-rice-new",
        "batch-meal": "batch-meal-new",
        "batch-curry": "batch-curry-new",
        "event-1": "event-new",
        "preview-1": "preview-new",
        "proposal-1": "proposal-new",
        "eval-session": "session-new",
        "seed-run-1": "seed-run-new",
        "seed-operation-1": "operation-new-1",
        "seed-operation-2": "operation-new-2",
    }

    def replace_ids(value):
        if isinstance(value, str):
            return replacements.get(value, value)
        if isinstance(value, list):
            return [replace_ids(item) for item in value]
        if isinstance(value, dict):
            return {key: replace_ids(item) for key, item in value.items()}
        return value

    renamed = replace_ids(renamed)
    assert normalize_state(original) == normalize_state(renamed)
    assert len(normalize_state(original)["operations"]) == 2


def test_normalization_preserves_operation_inputs_and_nonworkflow_history():
    from nutrition_eval.state import normalize_state

    original = db_payload(fixture_data())
    changed_input = deepcopy(original)
    changed_input["operations"][0]["input_hash"] = "different-input"
    assert normalize_state(original) != normalize_state(changed_input)

    state = {
        "events": [{"id": "event-1", "batch_id": "batch-1", "eaten_on": "2026-11-17", "meal": None, "boxes": 1, "data": {"history": ["business fact"]}}],
        "workflow_sessions": [{"id": "session-1", "data": {"stage": "idle", "history": [{"role": "user", "content": "transcript"}]}}],
    }
    normalized = normalize_state(state)
    assert normalized["events"][0]["data"]["history"] == ["business fact"]
    assert "history" not in normalized["workflow_sessions"][0]["data"]


def test_episode_schema_is_removed_after_success_and_exception():
    from nutrition_eval.fixtures import episode_store

    dsn = os.environ["TEST_DATABASE_URL"]
    with episode_store(dsn, "eval_cleanup") as store:
        success_schema = store.schema
    assert not schema_exists(dsn, success_schema)

    failed_schema = None
    with pytest.raises(RuntimeError, match="episode failure"):
        with episode_store(dsn, "eval_cleanup") as store:
            failed_schema = store.schema
            raise RuntimeError("episode failure")
    assert not schema_exists(dsn, failed_schema)


def test_fixture_loader_rejects_personal_database_and_nonempty_schema():
    from nutrition_eval.fixtures import episode_store, seed_fixture

    for dsn in (
        "postgresql://nutrition:unused@db/nutrition",
        "postgresql://nutrition:unused@db_test/nutrition",
    ):
        with pytest.raises(ValueError, match="TEST_DATABASE_URL.*db_test/nutrition_test"):
            with episode_store(dsn, "eval_unsafe"):
                raise AssertionError("unsafe database reached schema setup")

    dsn = os.environ["TEST_DATABASE_URL"]
    with episode_store(dsn, "eval_nonempty") as store:
        seed_fixture(store, fixture_data())
        with pytest.raises(ValueError, match="empty schema"):
            seed_fixture(store, fixture_data())


def test_fixture_loader_rejects_invalid_references_and_rolls_back():
    from nutrition_eval.fixtures import episode_store, seed_fixture

    dsn = os.environ["TEST_DATABASE_URL"]
    with episode_store(dsn, "eval_references") as store:
        invalid = fixture_data()
        invalid["batch_ingredients"][0]["cooking_ingredient_id"] = "missing-ingredient"
        with pytest.raises(ValueError, match="reference"):
            seed_fixture(store, invalid)

        seed_fixture(store, fixture_data())
