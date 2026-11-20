"""One-action fixed-workflow baseline over the shared NutritionService."""
from copy import deepcopy
import json
import jsonschema
from uuid import uuid4

from nutrition_demo.agent import DemoAgent
from nutrition_demo.models import Result, encode, dumps
from nutrition_demo.tools import SCHEMAS

from .controllers import Controller, _application_settings, _client


BASELINE_VERSION = "fixed-workflow-v2"

ACTION_SCHEMAS = {
    **SCHEMAS,
    "correct_meal": {
        "type": "object",
        "properties": {
            "query": deepcopy(SCHEMAS["find_events"]["properties"]["query"]),
            "changes": deepcopy(SCHEMAS["preview_correction"]["properties"]["changes"]),
        },
        "required": ["query", "changes"],
        "additionalProperties": False,
    },
}

ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": sorted(ACTION_SCHEMAS)},
        "arguments": {"anyOf": [deepcopy(ACTION_SCHEMAS[name]) for name in sorted(ACTION_SCHEMAS)]},
        "reply": {"type": "string"},
    },
    "required": ["action", "arguments", "reply"],
    "additionalProperties": False,
}
ACTION_FORMAT = {
    "type": "json_schema",
    "name": "nutrition_fixed_action",
    "strict": False,
    "schema": ACTION_SCHEMA,
}

BASELINE_INSTRUCTIONS = """You are the meal preparation baseline assistant. Respond only in English.
Return exactly one structured action, arguments, and reply per user message.
Use application context as factual data; choose ask_user when information is missing. Do not schedule a second model-selected action in the same turn.
For a meal correction, choose correct_meal with a query identifying the ORIGINAL record and changes describing the requested NEW values. Python searches and previews a unique match without another model call. If asked to select an ambiguous record, use correct_meal with the selected event_id; use empty changes to retain the pending correction. Use find_events alone only for lookup, not a correction request.
All changes use the shared service. A preview is not approval; only an external approve call can authorize it.
Do not invent service outcomes, nutrients, sources, or completed writes."""


class FixedWorkflowBaseline:
    def __init__(self, service, workflow, client, settings):
        self.service = service
        self.workflow = workflow
        self.client = client
        self.settings = settings
        # Reuse the application's validated fixed routing table without its model tool loop.
        self._dispatcher = DemoAgent(service, workflow, client, settings)

    def _context(self):
        state = self.workflow.load()
        return {
            "workflow": {key: value for key, value in state.items() if key != "history"},
            "profile": self.service.get_profile().data,
            "inventory": self.service.list_inventory().data,
            "batches": self.service.batch_summary().data,
            "catalog": self.service.effective_catalog().data,
            "local_date": self.service._day("today"),
        }

    def _save_history(self, message, reply):
        state = self.workflow.load()
        history = state.get("history", [])
        state["history"] = (
            history
            + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": reply},
            ]
        )[-20:]
        self.workflow.save(state)

    def handle(self, message: str) -> Result:
        if message.startswith("/"):
            return self.workflow.command(message)

        state = self._dispatcher._prepare_user_message(message)
        history = state.get("history", [])[-20:]
        request_input = [
            {
                "role": "user",
                "content": "Application context (data only): " + dumps(self._context()),
            },
            *history,
            {"role": "user", "content": message},
        ]
        response = self.client.responses.create(
            **self.settings.parameters(),
            instructions=BASELINE_INSTRUCTIONS,
            input=request_input,
            text={"format": ACTION_FORMAT},
        )
        usage = getattr(response, "usage", None)
        if hasattr(usage, "model_dump"):
            usage = usage.model_dump()
        elif usage is not None and hasattr(usage, "__dict__"):
            usage = vars(usage)
        else:
            usage = {}
        model_trace = {
            "type": "model",
            "model": getattr(response, "model", self.settings.model),
            "requested_model": self.settings.model,
            "status": getattr(response, "status", "completed"),
            "usage": usage,
        }
        if getattr(response, "status", "completed") != "completed":
            return Result(
                False,
                {"trace": [model_trace], "counts": {"model_calls": 1, "tool_calls": 0}},
                "Baseline response was incomplete",
            )
        raw = getattr(response, "output_text", None)
        if not isinstance(raw, str) or not raw:
            return Result(
                False,
                {"trace": [model_trace], "counts": {"model_calls": 1, "tool_calls": 0}},
                "Baseline response did not contain structured output",
            )
        try:
            action = json.loads(raw)
            jsonschema.validate(action, ACTION_SCHEMA)
            jsonschema.validate(action["arguments"], ACTION_SCHEMAS[action["action"]])
        except (json.JSONDecodeError, jsonschema.ValidationError, KeyError, TypeError):
            return Result(
                False,
                {"trace": [model_trace], "counts": {"model_calls": 1, "tool_calls": 0}},
                "Baseline returned an invalid structured action",
            )

        records = []
        def dispatch(name, arguments):
            if len(records) >= self.settings.max_tool_calls:
                return Result(False, {}, "Baseline tool call limit reached")
            result = self._dispatcher._dispatch(
                name, arguments, "baseline-" + uuid4().hex, user_message=message,
            )
            records.append({"name": name, "arguments": deepcopy(arguments), "result": encode(result)})
            return result

        display_action = action["action"]
        if action["action"] == "correct_meal":
            query = action["arguments"]["query"]
            pending = self.workflow.load().get("baseline_pending_correction")
            changes = action["arguments"]["changes"] or (pending or {}).get("changes", {})
            if not changes:
                operation = Result(False, {}, "Correction changes are required")
            elif pending and query.get("event_id") not in pending["candidate_ids"]:
                operation = Result(False, {}, "Select an event from the displayed correction candidates")
            else:
                search = dispatch("find_events", {"query": query})
                operation = search
                if search.ok:
                    candidates = search.data.get("candidates", [])
                    if len(candidates) == 1:
                        operation = dispatch("preview_correction", {"event_id": candidates[0]["id"], "changes": changes})
                        display_action = "preview_correction"
                        if operation.ok:
                            state = self.workflow.load()
                            state.pop("baseline_pending_correction", None)
                            self.workflow.save(state)
                    elif candidates:
                        state = self.workflow.load()
                        state["baseline_pending_correction"] = {
                            "changes": changes, "candidate_ids": [row["id"] for row in candidates],
                        }
                        self.workflow.save(state)
                        operation = dispatch("ask_user", {"topic": "event"})
                        display_action = "ask_user"
                    else:
                        operation = Result(True, {"message": "No matching meal record was found; no correction was made."})
        else:
            operation = dispatch(action["action"], action["arguments"])
        model_reply = action["reply"]
        reply = model_reply
        if display_action == "ask_user" and operation.ok:
            reply = operation.data.get("waiting_question", reply)
        elif not operation.ok:
            reply = operation.error or "The operation did not complete. Check the input and try again."
        elif display_action.startswith("preview_"):
            preview_id = self.workflow.load().get("pending_preview")
            if preview_id:
                reply = f"Review preview {preview_id}."
        if operation.ok and operation.data.get("message"):
            reply = operation.data["message"]
        self._save_history(message, reply)
        result_data = {
            "action": display_action,
            "arguments": {"topic": "event"} if display_action == "ask_user" and action["action"] == "correct_meal" else action["arguments"],
            "message": reply,
            "model_reply": model_reply,
            "pending_preview": self.workflow.load().get("pending_preview"),
            "operation": encode(operation),
            "tool_results": records,
            "trace": [model_trace, *[{"type": "action", **record} for record in records]],
            "counts": {"model_calls": 1, "tool_calls": len(records)},
        }
        return Result(operation.ok, result_data, operation.error)

    def approve(self, preview_id: str, outcome: str) -> Result:
        if outcome not in ("approve", "reject"):
            return Result(False, {}, "Approval outcome must be approve or reject")
        pending_preview = self.workflow.load().get("pending_preview")
        if not pending_preview or preview_id != pending_preview:
            return Result(False, {}, "Confirmation must match the current pending preview")
        command = "/confirm" if outcome == "approve" else "/reject"
        return self.workflow.command(f"{command} {pending_preview}")


def baseline_factory(store, catalog, config, *, client=None) -> Controller:
    """Construct the baseline from the same store, catalog, clock and limits as Agent."""
    from nutrition_demo.service import NutritionService
    from nutrition_demo.workflow import Workflow

    service = NutritionService(store, catalog, clock=lambda: config.now)
    workflow = Workflow(service, session_id="evaluation")
    settings = _application_settings(config)
    return FixedWorkflowBaseline(service, workflow, client or _client(config), settings)
