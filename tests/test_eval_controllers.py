import json
from copy import deepcopy
import inspect

from nutrition_demo.models import Result


class FakeWorkflow:
    def __init__(self, state=None):
        self.commands = []
        self.state = state or {
            "stage": "ready",
            "clarifications": 0,
            "pending_preview": None,
            "history": [],
        }

    def load(self):
        return deepcopy(self.state)

    def save(self, state):
        self.state = deepcopy(state)

    def command(self, message):
        self.commands.append(message)
        return Result(True, {"command": message})


class FakeResponses:
    def __init__(self, *actions):
        self.actions = list(actions)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return FakeResponse(self.actions.pop(0))


class FakeResponse:
    status = "completed"
    model = "test-model"
    usage = None

    def __init__(self, action):
        self.output_text = json.dumps(action)


class FakeClient:
    def __init__(self, *actions):
        self.responses = FakeResponses(*actions)


class SpyService:
    def __init__(self):
        self.calls = []
        self.preview_count = 0

    def get_profile(self):
        return Result(True, {"timezone": "America/Los_Angeles"})

    def list_inventory(self):
        self.calls.append(("list_inventory", {}))
        return Result(True, {"items": []})

    def batch_summary(self):
        return Result(True, {"batches": []})

    def effective_catalog(self):
        return Result(True, {"recipes": []})

    def _day(self, _day):
        return "2026-11-18"

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)

        def call(**kwargs):
            self.calls.append((name, deepcopy(kwargs)))
            if name.startswith("preview_"):
                self.preview_count += 1
                return Result(True, {"id": f"preview-{self.preview_count}", "kind": name.removeprefix("preview_")})
            return Result(True, {"operation": name})

        return call


def test_agent_adapter_passes_message_and_preview_id_to_application_confirmation():
    from nutrition_eval.controllers import AgentController

    class Agent:
        def __init__(self):
            self.messages = []

        def handle(self, message):
            self.messages.append(message)
            return Result(True, {"message": message})

    workflow = FakeWorkflow({"pending_preview": "preview-current"})
    agent = Agent()
    controller = AgentController(agent, workflow)

    result = controller.handle("show my inventory")
    approved = controller.approve("preview-current", "approve")
    rejected = controller.approve("preview-current", "reject")
    mismatch = controller.approve("preview-other", "approve")

    assert result.ok
    assert approved.ok and rejected.ok
    assert agent.messages == [
        "show my inventory",
        "/confirm preview-current",
        "/reject preview-current",
    ]
    assert not mismatch.ok


def test_controller_factory_receives_catalog_but_no_task_or_rubric():
    from nutrition_eval.controllers import agent_factory
    from nutrition_eval.baseline import baseline_factory

    for factory in (agent_factory, baseline_factory):
        parameters = list(inspect.signature(factory).parameters.values())
        assert [parameter.name for parameter in parameters[:3]] == ["store", "catalog", "config"]
        assert "task" not in inspect.signature(factory).parameters
        assert "expected_changes" not in inspect.signature(factory).parameters
        assert "reply_rubric" not in inspect.signature(factory).parameters


def test_fixed_baseline_uses_closed_action_schema_and_one_route_per_response():
    from nutrition_demo.agent import Settings
    from nutrition_demo.tools import SCHEMAS
    from nutrition_eval.baseline import ACTION_SCHEMA, FixedWorkflowBaseline

    service = SpyService()
    workflow = FakeWorkflow()
    client = FakeClient({"action": "list_inventory", "arguments": {}, "reply": "目前庫存如下。"})
    baseline = FixedWorkflowBaseline(service, workflow, client, Settings())

    result = baseline.handle("show my inventory")

    assert result.ok
    assert len(client.responses.calls) == 1
    assert [item["type"] for item in result.data["trace"]] == ["model", "action"]
    assert result.data["action"] == "list_inventory"
    schema = client.responses.calls[0]["text"]["format"]["schema"]
    assert schema == ACTION_SCHEMA
    assert schema["properties"]["action"]["enum"] == sorted(SCHEMAS)
    assert schema["additionalProperties"] is False
    assert "expected_changes" not in json.dumps(client.responses.calls[0]["input"])
    assert all(branch["additionalProperties"] is False for branch in schema["properties"]["arguments"]["anyOf"])


def test_baseline_uses_same_service_for_inventory_meal_and_correction():
    from nutrition_demo.agent import Settings
    from nutrition_eval.baseline import FixedWorkflowBaseline

    service = SpyService()
    workflow = FakeWorkflow()
    client = FakeClient(
        {"action": "list_inventory", "arguments": {}, "reply": "庫存查詢完成。"},
        {
            "action": "preview_reconciled_meal",
            "arguments": {
                "items": [],
                "meal_input": {"batch_id": "batch-1", "eaten_on": "2026-11-17", "meal": "dinner", "addon_override": None},
                "mode": "reconcile",
            },
            "reply": "已檢查餐點資料。",
        },
        {
            "action": "preview_correction",
            "arguments": {"event_id": "event-1", "changes": {}},
            "reply": "已檢查更正內容。",
        },
    )
    baseline = FixedWorkflowBaseline(service, workflow, client, Settings())

    results = [
        baseline.handle("show inventory"),
        baseline.handle("preview this meal"),
        baseline.handle("preview this correction"),
    ]

    assert [result.data["action"] for result in results] == [
        "list_inventory",
        "preview_reconciled_meal",
        "preview_correction",
    ]
    assert len(client.responses.calls) == 3
    names = [name for name, _ in service.calls]
    assert names.count("list_inventory") == 4  # context read for each message plus the selected action
    assert names.count("preview_reconciled_meal") == 1
    assert names.count("preview_correction") == 1


def test_baseline_rejects_arguments_outside_the_selected_action_schema():
    from nutrition_demo.agent import Settings
    from nutrition_eval.baseline import FixedWorkflowBaseline

    service = SpyService()
    baseline = FixedWorkflowBaseline(
        service,
        FakeWorkflow(),
        FakeClient({
            "action": "preview_correction",
            "arguments": {"event_id": "event-1", "changes": {}, "approve": True},
            "reply": "已完成。",
        }),
        Settings(),
    )

    result = baseline.handle("correct this meal")

    assert not result.ok
    assert result.data["counts"] == {"model_calls": 1, "tool_calls": 0}
    assert all(name != "preview_correction" for name, _ in service.calls)


def test_baseline_approval_uses_only_the_current_preview_id():
    from nutrition_demo.agent import Settings
    from nutrition_eval.baseline import FixedWorkflowBaseline

    workflow = FakeWorkflow({"pending_preview": "preview-current"})
    baseline = FixedWorkflowBaseline(SpyService(), workflow, FakeClient(), Settings())

    approved = baseline.approve("preview-current", "approve")
    mismatch = baseline.approve("preview-old", "approve")

    assert approved.ok
    assert workflow.commands == ["/confirm preview-current"]
    assert not mismatch.ok
