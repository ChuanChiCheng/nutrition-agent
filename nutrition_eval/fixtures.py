from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
import re
from typing import Iterator
from uuid import uuid4

import psycopg
from psycopg import IntegrityError
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

from nutrition_demo.models import decimal
from nutrition_demo.store import TABLES, Store, jsonb


_FIXTURE_KEYS = {
    "synthetic",
    "provenance",
    "catalog",
    "profile",
    "inventory",
    "cooking_runs",
    "cooking_ingredients",
    "batches",
    "batch_ingredients",
    "batch_addons",
    "events",
    "inventory_movements",
    "previews",
    "operations",
    "workflow_sessions",
}
_ROW_TABLES = (
    "inventory",
    "cooking_runs",
    "cooking_ingredients",
    "batches",
    "batch_ingredients",
    "batch_addons",
    "events",
    "inventory_movements",
    "previews",
    "operations",
    "workflow_sessions",
)


def _test_database_info(dsn: str) -> dict:
    if not dsn:
        raise ValueError("TEST_DATABASE_URL is required; never fall back to DATABASE_URL")
    try:
        info = conninfo_to_dict(dsn)
    except (TypeError, ValueError) as exc:
        raise ValueError("TEST_DATABASE_URL is invalid") from exc
    if info.get("host") != "db_test" or info.get("dbname") != "nutrition_test":
        raise ValueError("TEST_DATABASE_URL must point to db_test/nutrition_test")
    return info


def _rows(fixture: dict, key: str) -> list[dict]:
    rows = fixture.get(key, [])
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"fixture {key} must be a list of objects")
    return rows


@contextmanager
def episode_store(dsn: str, schema_prefix: str) -> Iterator[Store]:
    """Create an isolated schema in the dedicated test database and always drop it."""
    _test_database_info(dsn)
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,20}", schema_prefix):
        raise ValueError("schema_prefix must be a short lowercase SQL identifier")

    schema = f"{schema_prefix}_{uuid4().hex}"
    with psycopg.connect(dsn, autocommit=True, connect_timeout=5) as connection:
        connection.execute(
            sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema))
        )

    store = Store(dsn, schema)
    try:
        store.migrate()
        yield store
    finally:
        store.close()
        with psycopg.connect(dsn, autocommit=True, connect_timeout=5) as connection:
            connection.execute(
                sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema))
            )


def seed_fixture(store: Store, fixture: dict) -> None:
    """Seed a synthetic episode fixture atomically into a freshly migrated schema."""
    if not isinstance(fixture, dict):
        raise ValueError("fixture must be an object")
    if fixture.get("synthetic") is not True:
        raise ValueError("fixture must explicitly declare synthetic=true")
    unknown = set(fixture) - _FIXTURE_KEYS
    if unknown:
        raise ValueError(f"unsupported fixture fields: {', '.join(sorted(unknown))}")

    rows = {key: _rows(fixture, key) for key in _ROW_TABLES}
    profile = fixture.get("profile")
    if profile is not None and not isinstance(profile, dict):
        raise ValueError("fixture profile must be an object or null")

    try:
        with store.transaction(lock=True) as connection:
            present = any(
                connection.execute(
                        sql.SQL("SELECT EXISTS(SELECT 1 FROM {}) AS present").format(sql.Identifier(table))
                    ).fetchone()["present"]
                for table in TABLES
            )
            if present:
                raise ValueError("fixture loader requires an empty schema")

            if profile is not None:
                connection.execute(
                    "INSERT INTO profile(id,data) VALUES(1,%s)", (jsonb(profile),)
                )

            for item in rows["inventory"]:
                connection.execute(
                    "INSERT INTO inventory(ingredient_id,quantity,unit,state,data) "
                    "VALUES(%s,%s,%s,%s,%s)",
                    (
                        item["ingredient_id"],
                        decimal(item["quantity"]),
                        item["unit"],
                        item["state"],
                        jsonb(item.get("source", {"status": "synthetic"})),
                    ),
                )

            for run in rows["cooking_runs"]:
                connection.execute(
                    "INSERT INTO cooking_runs(id,recipe_id,prepared_on,request_id,data) "
                    "VALUES(%s,%s,%s,%s,%s)",
                    (run["id"], run["recipe_id"], run["prepared_on"], run["request_id"], jsonb(run["data"])),
                )

            for ingredient in rows["cooking_ingredients"]:
                connection.execute(
                    "INSERT INTO cooking_ingredients(id,cooking_run_id,ingredient_id,quantity,unit,data) "
                    "VALUES(%s,%s,%s,%s,%s,%s)",
                    (
                        ingredient["id"],
                        ingredient["cooking_run_id"],
                        ingredient["ingredient_id"],
                        decimal(ingredient["quantity"]),
                        ingredient["unit"],
                        jsonb(ingredient["data"]),
                    ),
                )

            for batch in rows["batches"]:
                connection.execute(
                    "INSERT INTO batches(id,cooking_run_id,name,total_boxes,remaining_boxes,data) "
                    "VALUES(%s,%s,%s,%s,%s,%s)",
                    (
                        batch["id"],
                        batch["cooking_run_id"],
                        batch["name"],
                        batch["total_boxes"],
                        batch["remaining_boxes"],
                        jsonb(batch["data"]),
                    ),
                )

            for allocation in rows["batch_ingredients"]:
                connection.execute(
                    "INSERT INTO batch_ingredients(batch_id,cooking_ingredient_id,quantity,unit) "
                    "VALUES(%s,%s,%s,%s)",
                    (
                        allocation["batch_id"],
                        allocation["cooking_ingredient_id"],
                        decimal(allocation["quantity"]),
                        allocation["unit"],
                    ),
                )

            for addon_plan in rows["batch_addons"]:
                connection.execute(
                    "INSERT INTO batch_addons(batch_id,version,data) VALUES(%s,%s,%s)",
                    (addon_plan["batch_id"], addon_plan["version"], jsonb({"items": addon_plan["items"]})),
                )

            for event in rows["events"]:
                connection.execute(
                    "INSERT INTO events(id,batch_id,eaten_on,meal,boxes,data) VALUES(%s,%s,%s,%s,%s,%s)",
                    (
                        event["id"],
                        event["batch_id"],
                        event["eaten_on"],
                        event.get("meal"),
                        event.get("boxes", 1),
                        jsonb(event["data"]),
                    ),
                )

            for movement in rows["inventory_movements"]:
                try:
                    delta = Decimal(str(movement["delta"]))
                except (InvalidOperation, TypeError, ValueError) as exc:
                    raise ValueError("inventory movement delta must be a finite number") from exc
                if not delta.is_finite():
                    raise ValueError("inventory movement delta must be a finite number")
                connection.execute(
                    "INSERT INTO inventory_movements(ingredient_id,delta,cooking_run_id,event_id,kind,data) "
                    "VALUES(%s,%s,%s,%s,%s,%s)",
                    (
                        movement["ingredient_id"],
                        delta,
                        movement.get("cooking_run_id"),
                        movement.get("event_id"),
                        movement["kind"],
                        jsonb(movement.get("data", {})),
                    ),
                )

            for preview in rows["previews"]:
                connection.execute(
                    "INSERT INTO previews(id,kind,state_version,status,data,created_at,confirmed_at) "
                    "VALUES(%s,%s,%s,%s,%s,COALESCE(%s::timestamptz,CURRENT_TIMESTAMP),%s)",
                    (
                        preview["id"],
                        preview["kind"],
                        preview["state_version"],
                        preview.get("status", "pending"),
                        jsonb(preview["data"]),
                        preview.get("created_at"),
                        preview.get("confirmed_at"),
                    ),
                )

            for operation in rows["operations"]:
                connection.execute(
                    "INSERT INTO operations(request_id,input_hash,result) VALUES(%s,%s,%s)",
                    (operation["request_id"], operation["input_hash"], jsonb(operation["result"])),
                )

            for session in rows["workflow_sessions"]:
                connection.execute(
                    "INSERT INTO workflow_sessions(id,data) VALUES(%s,%s)",
                    (session["id"], jsonb(session["data"])),
                )

            connection.execute("UPDATE state_meta SET version=version+1 WHERE id=1")
    except IntegrityError as exc:
        raise ValueError("fixture contains an invalid reference or violates a database constraint") from exc
