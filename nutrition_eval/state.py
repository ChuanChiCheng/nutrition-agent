from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any

from nutrition_demo.store import Store


_VOLATILE_KEYS = {
    "request_id",
    "run_id",
    "created_at",
    "updated_at",
    "confirmed_at",
}


def _decimal_text(value: Decimal) -> str:
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def _stable(value: Any, id_maps: dict[str, dict[str, str]] | None = None, key: str | None = None):
    id_maps = id_maps or {}
    if isinstance(value, Decimal):
        return _decimal_text(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        result = {}
        for child_key, child_value in value.items():
            if child_key in _VOLATILE_KEYS:
                continue
            result[child_key] = _stable(child_value, id_maps, child_key)
        return result
    if isinstance(value, (list, tuple)):
        if key == "batch_ids":
            return [id_maps.get("batches", {}).get(item, item) for item in value]
        return [_stable(item, id_maps) for item in value]
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("business state contains a non-finite number")
        return _decimal_text(Decimal(str(value)))
    if isinstance(value, str) and key:
        mapping_name = {
            "cooking_run_id": "cooking_runs",
            "batch_id": "batches",
            "cooking_ingredient_id": "cooking_ingredients",
            "event_id": "events",
            "pending_preview": "previews",
            "preview_id": "previews",
            "rejected": "previews",
            "accepted_recipe": "proposals",
            "id": "proposals",
        }.get(key)
        if mapping_name:
            return id_maps.get(mapping_name, {}).get(value, value)
    return value


def _sort_key(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _semantic_id(kind: str, value: Any) -> str:
    digest = sha256(_sort_key(value).encode("utf-8")).hexdigest()[:20]
    return f"{kind}:{digest}"


def read_business_state(store: Store) -> dict:
    """Read all semantic application tables; agent-run telemetry is excluded."""
    with store.transaction() as connection:
        profile_row = connection.execute("SELECT data FROM profile WHERE id=1").fetchone()
        inventory = [
            {
                "ingredient_id": row["ingredient_id"],
                "quantity": row["quantity"],
                "unit": row["unit"],
                "state": row["state"],
                "source": row["data"],
            }
            for row in connection.execute("SELECT * FROM inventory ORDER BY ingredient_id").fetchall()
        ]
        cooking_runs = connection.execute(
            "SELECT id,recipe_id,prepared_on,request_id,data FROM cooking_runs"
        ).fetchall()
        cooking_ingredients = connection.execute(
            "SELECT id,cooking_run_id,ingredient_id,quantity,unit,data FROM cooking_ingredients"
        ).fetchall()
        batches = connection.execute(
            "SELECT id,cooking_run_id,name,total_boxes,remaining_boxes,data FROM batches"
        ).fetchall()
        batch_ingredients = connection.execute(
            "SELECT batch_id,cooking_ingredient_id,quantity,unit FROM batch_ingredients"
        ).fetchall()
        batch_addons = connection.execute(
            "SELECT batch_id,version,data FROM batch_addons"
        ).fetchall()
        events = connection.execute(
            "SELECT id,batch_id,eaten_on,meal,boxes,data FROM events"
        ).fetchall()
        movements = connection.execute(
            "SELECT ingredient_id,delta,cooking_run_id,event_id,kind,data FROM inventory_movements"
        ).fetchall()
        previews = connection.execute(
            "SELECT id,kind,state_version,status,data,created_at,confirmed_at FROM previews"
        ).fetchall()
        operations = connection.execute(
            "SELECT request_id,input_hash,result,created_at FROM operations"
        ).fetchall()
        workflow_sessions = connection.execute(
            "SELECT id,data,updated_at FROM workflow_sessions"
        ).fetchall()

    return {
        "profile": profile_row["data"] if profile_row else None,
        "inventory": inventory,
        "cooking_runs": [dict(row) for row in cooking_runs],
        "cooking_ingredients": [dict(row) for row in cooking_ingredients],
        "batches": [dict(row) for row in batches],
        "batch_ingredients": [dict(row) for row in batch_ingredients],
        "batch_addons": [
            {"batch_id": row["batch_id"], "version": row["version"], "items": row["data"]["items"]}
            for row in batch_addons
        ],
        "events": [dict(row) for row in events],
        "inventory_movements": [dict(row) for row in movements],
        "previews": [dict(row) for row in previews],
        "operations": [dict(row) for row in operations],
        "workflow_sessions": [dict(row) for row in workflow_sessions],
    }


def normalize_state(state: dict) -> dict:
    """Normalize generated IDs/timestamps without losing rows or relationships."""
    id_maps: dict[str, dict[str, str]] = {
        "cooking_runs": {},
        "cooking_ingredients": {},
        "batches": {},
        "events": {},
        "previews": {},
        "proposals": {},
    }

    runs = state.get("cooking_runs", [])
    for row in runs:
        semantic = _stable(
            {"recipe_id": row["recipe_id"], "prepared_on": row["prepared_on"], "data": row["data"]},
            id_maps,
        )
        id_maps["cooking_runs"][row["id"]] = _semantic_id("run", semantic)

    for row in state.get("cooking_ingredients", []):
        semantic = _stable(
            {
                "cooking_run_id": row["cooking_run_id"],
                "ingredient_id": row["ingredient_id"],
                "quantity": row["quantity"],
                "unit": row["unit"],
                "data": row["data"],
            },
            id_maps,
        )
        id_maps["cooking_ingredients"][row["id"]] = _semantic_id("cooking-ingredient", semantic)

    for row in state.get("batches", []):
        semantic = _stable(
            {
                "cooking_run_id": row["cooking_run_id"],
                "name": row["name"],
                "total_boxes": row["total_boxes"],
                "data": row["data"],
            },
            id_maps,
        )
        id_maps["batches"][row["id"]] = _semantic_id("batch", semantic)

    for row in state.get("events", []):
        semantic = _stable(
            {
                "batch_id": row["batch_id"],
                "eaten_on": row["eaten_on"],
                "meal": row["meal"],
                "boxes": row.get("boxes", 1),
                "data": row["data"],
            },
            id_maps,
        )
        id_maps["events"][row["id"]] = _semantic_id("event", semantic)

    for row in state.get("previews", []):
        semantic = _stable(
            {"kind": row["kind"], "status": row["status"], "data": row["data"]},
            id_maps,
        )
        id_maps["previews"][row["id"]] = _semantic_id("preview", semantic)

    for session in state.get("workflow_sessions", []):
        proposal = session.get("data", {}).get("proposal")
        if isinstance(proposal, dict) and isinstance(proposal.get("id"), str):
            semantic_proposal = {key: value for key, value in proposal.items() if key != "id"}
            id_maps["proposals"][proposal["id"]] = _semantic_id(
                "proposal", _stable(semantic_proposal, id_maps)
            )

    normalized = {
        "profile": _stable(state.get("profile"), id_maps),
        "inventory": [
            _stable(row, id_maps) for row in state.get("inventory", [])
        ],
        "cooking_runs": [
            _stable(
                {"recipe_id": row["recipe_id"], "prepared_on": row["prepared_on"], "data": row["data"]},
                id_maps,
            )
            for row in runs
        ],
        "cooking_ingredients": [
            _stable(
                {
                    "cooking_run_id": row["cooking_run_id"],
                    "ingredient_id": row["ingredient_id"],
                    "quantity": row["quantity"],
                    "unit": row["unit"],
                    "data": row["data"],
                },
                id_maps,
            )
            for row in state.get("cooking_ingredients", [])
        ],
        "batches": [
            _stable(
                {
                    "cooking_run_id": row["cooking_run_id"],
                    "name": row["name"],
                    "total_boxes": row["total_boxes"],
                    "remaining_boxes": row["remaining_boxes"],
                    "data": row["data"],
                },
                id_maps,
            )
            for row in state.get("batches", [])
        ],
        "batch_ingredients": [
            _stable(
                {
                    "batch_id": row["batch_id"],
                    "cooking_ingredient_id": row["cooking_ingredient_id"],
                    "quantity": row["quantity"],
                    "unit": row["unit"],
                },
                id_maps,
            )
            for row in state.get("batch_ingredients", [])
        ],
        "batch_addons": [
            _stable(
                {"batch_id": row["batch_id"], "version": row["version"], "items": row["items"]},
                id_maps,
            )
            for row in state.get("batch_addons", [])
        ],
        "events": [
            _stable(
                {
                    "batch_id": row["batch_id"],
                    "eaten_on": row["eaten_on"],
                    "meal": row.get("meal"),
                    "boxes": row.get("boxes", 1),
                    "data": row["data"],
                },
                id_maps,
            )
            for row in state.get("events", [])
        ],
        "inventory_movements": [
            _stable(
                {
                    "ingredient_id": row["ingredient_id"],
                    "delta": row["delta"],
                    "cooking_run_id": row.get("cooking_run_id"),
                    "event_id": row.get("event_id"),
                    "kind": row["kind"],
                    "data": row["data"],
                },
                id_maps,
            )
            for row in state.get("inventory_movements", [])
        ],
        "previews": [
            _stable(
                {
                    "kind": row["kind"],
                    "state_version": row["state_version"],
                    "status": row["status"],
                    "data": row["data"],
                },
                id_maps,
            )
            for row in state.get("previews", [])
        ],
        "operations": [
            _stable({"input_hash": row["input_hash"], "result": row["result"]}, id_maps)
            for row in state.get("operations", [])
        ],
        # Conversation history is graded from the trace/reply; application workflow fields remain here.
        "workflow_sessions": [
            _stable(
                {"data": {key: value for key, value in row["data"].items() if key != "history"}},
                id_maps,
            )
            for row in state.get("workflow_sessions", [])
        ],
    }
    for key, rows in normalized.items():
        if isinstance(rows, list):
            rows.sort(key=_sort_key)
    return normalized
