"""One-action fixed-workflow baseline over the shared NutritionService."""
from copy import deepcopy
import json
import jsonschema
from uuid import uuid4

from nutrition_demo.agent import DemoAgent
from nutrition_demo.models import Result, encode, dumps
from nutrition_demo.tools import SCHEMAS

from .controllers import Controller, _application_settings, _client


ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": sorted(SCHEMAS)},
        "arguments": {"anyOf": [deepcopy(SCHEMAS[name]) for name in sorted(SCHEMAS)]},
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
Use application context as factual data; choose ask_user when information is missing. Do not schedule a second action in the same turn.
All changes use the shared service. A preview is not approval; only an external approve call can authorize it.
Do not invent service outcomes, nutrients, sources, or completed writes."""


class FixedWorkflowBaseline:
    def __init__(self, service, workflow, client, settings):
        self.service = service
        self.workflow = workflow
        self.client = client
        self.settings = settings
        # Reuse the application's validated fixed routing table without its model tool loop.
        from .english import EnglishAgent
        self._dispatcher = EnglishAgent(service, workflow, client, settings)

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

        state = self.workflow.load()
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
            jsonschema.validate(action["arguments"], SCHEMAS[action["action"]])
        except (json.JSONDecodeError, jsonschema.ValidationError, KeyError, TypeError):
            return Result(
                False,
                {"trace": [model_trace], "counts": {"model_calls": 1, "tool_calls": 0}},
                "Baseline returned an invalid structured action",
            )

        operation = self._dispatcher._dispatch(
            action["action"],
            action["arguments"],
            "baseline-" + uuid4().hex,
            user_message=message,
        )
        model_reply = action["reply"]
        reply = model_reply
        if action["action"] == "ask_user" and operation.ok:
            reply = operation.data.get("waiting_question", reply)
        elif not operation.ok:
            reply = operation.error or "The operation did not complete. Check the input and try again."
        elif action["action"].startswith("preview_"):
            preview_id = self.workflow.load().get("pending_preview")
            if preview_id:
                reply = f"Review preview {preview_id}."
        self._save_history(message, reply)
        result_data = {
            "action": action["action"],
            "arguments": action["arguments"],
            "message": reply,
            "model_reply": model_reply,
            "pending_preview": self.workflow.load().get("pending_preview"),
            "operation": encode(operation),
            "trace": [
                model_trace,
                {
                    "type": "action",
                    "name": action["action"],
                    "arguments": action["arguments"],
                    "result": encode(operation),
                },
            ],
            "counts": {"model_calls": 1, "tool_calls": 1},
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
    from .english import EnglishService as NutritionService, EnglishWorkflow as Workflow

    service = NutritionService(store, catalog, clock=lambda: config.now)
    workflow = Workflow(service, session_id="evaluation")
    settings = _application_settings(config)
    return FixedWorkflowBaseline(service, workflow, client or _client(config), settings)
