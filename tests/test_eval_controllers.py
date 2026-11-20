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
    from nutrition_eval.baseline import ACTION_SCHEMA, ACTION_SCHEMAS, FixedWorkflowBaseline

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
    assert schema["properties"]["action"]["enum"] == sorted(ACTION_SCHEMAS)
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


def test_baseline_preserves_consumption_context_across_batch_clarification():
    from nutrition_demo.agent import Settings
    from nutrition_eval.baseline import FixedWorkflowBaseline
    service=SpyService()
    service.batch_summary=lambda: Result(True,{'batches':[
        {'id':'batch-1','name':'Lunch batch','remaining_boxes':2},
        {'id':'batch-2','name':'Dinner batch','remaining_boxes':2}]})
    client=FakeClient(
        {'action':'ask_user','arguments':{'topic':'batch'},'reply':'Which batch?'},
        {'action':'log_meal','arguments':{'batch_id':'batch-1','eaten_on':'today','meal':'dinner','addon_override':None},'reply':'Recorded.'})
    baseline=FixedWorkflowBaseline(service,FakeWorkflow(),client,Settings())
    assert baseline.handle('I ate one box for dinner today.').ok
    assert baseline.handle('Lunch batch.').ok
    assert any(name=='log_meal' for name,args in service.calls)
    assert baseline.workflow.load().get('pending_consumption') is None


def test_baseline_correction_search_continues_to_preview_without_second_model_call():
    from nutrition_demo.agent import Settings
    from nutrition_demo.display import render
    from nutrition_eval.baseline import FixedWorkflowBaseline
    service=SpyService()
    service.find_events=lambda query: Result(True,{'candidates':[{'id':'event-1'}],'needs_clarification':False})
    client=FakeClient({'action':'correct_meal','arguments':{
        'query':{'date':'2026-11-17','meal':'lunch'},'changes':{'date':'2026-11-18','meal':'breakfast'}},'reply':'Review correction.'})
    baseline=FixedWorkflowBaseline(service,FakeWorkflow(),client,Settings())
    result=baseline.handle('Move the November 17 lunch to November 18 breakfast.')
    assert result.ok
    assert len(client.responses.calls)==1
    assert ('preview_correction',{'event_id':'event-1','changes':{'date':'2026-11-18','meal':'breakfast'}}) in service.calls
    assert [t['name'] for t in result.data['trace'] if t['type']=='action']==['find_events','preview_correction']
    assert result.data['counts']['tool_calls']==2
    assert 'preview-1' in render(result)


def test_baseline_ambiguous_correction_asks_before_preview():
    from nutrition_demo.agent import Settings
    from nutrition_eval.baseline import FixedWorkflowBaseline
    service=SpyService()
    service.find_events=lambda query: Result(True,{'candidates':[{'id':'event-1'},{'id':'event-2'}],'needs_clarification':True})
    client=FakeClient({'action':'correct_meal','arguments':{'query':{'date':'2026-11-17'},'changes':{'meal':'breakfast'}},'reply':'Choose a record.'})
    baseline=FixedWorkflowBaseline(service,FakeWorkflow(),client,Settings())
    result=baseline.handle('Correct yesterday to breakfast.')
    assert result.ok
    assert result.data['action']=='ask_user'
    from nutrition_eval.episode import _explicit_ask_user
    assert _explicit_ask_user(result)['arguments']=={'topic':'event'}
    assert baseline.workflow.load()['baseline_pending_correction']['changes']=={'meal':'breakfast'}
    assert not any(name=='preview_correction' for name,args in service.calls)


def test_baseline_preview_renders_service_changes_not_only_id():
    from nutrition_demo.agent import Settings
    from nutrition_demo.display import render
    from nutrition_eval.baseline import FixedWorkflowBaseline
    service=SpyService()
    service.preview_inventory_change=lambda **kwargs: Result(True,{'id':'preview-stock','kind':'inventory',
        'summary':'Confirm inventory change.','changes':[{'ingredient_id':'rice','before':'5','after':'10','unit':'g'}]})
    client=FakeClient({'action':'preview_inventory_change','arguments':{'items':[],'mode':'reconcile'},'reply':'Review.'})
    result=FixedWorkflowBaseline(service,FakeWorkflow(),client,Settings()).handle('Correct rice stock to 10 g.')
    text=render(result)
    assert 'rice' in text and '5' in text and '10' in text and 'Confirm inventory change.' in text


def test_baseline_replays_m08_and_all_corrections_against_real_database():
    import os
    import re
    from pathlib import Path
    from nutrition_eval.fixtures import episode_store, seed_fixture
    from nutrition_eval.runner import _catalog_from_fixture
    from nutrition_eval.baseline import baseline_factory
    from nutrition_eval.__main__ import _load_config
    from nutrition_eval.tasks import load_tasks
    from nutrition_eval.episode import run_episode
    from nutrition_eval.grading import grade_state, grade_order

    root=Path(__file__).resolve().parents[1]
    _,config=_load_config(root/'eval_config.json')
    cases=[t for t in load_tasks(root/'tasks.jsonl') if t.id=='M08' or t.category=='corrections']
    assert len(cases)==11
    for task in cases:
        if task.id=='M08':
            actions=[{'action':'ask_user','arguments':{'topic':'batch'},'reply':'Which batch?'},
                {'action':'log_meal','arguments':{'batch_id':'batch-1','eaten_on':'2026-11-18','meal':'dinner','addon_override':None},'reply':'Recorded.'}]
        else:
            date=re.search(r'2026-\d\d-\d\d',task.request).group()
            meal=next(m for m in ['breakfast','dinner','snack'] if m in task.request)
            actions=[{'action':'correct_meal','arguments':{'query':{'date':'2026-11-17','meal':'lunch'},'changes':{'date':date,'meal':meal}},'reply':'Review the correction.'}]
        client=FakeClient(*actions)
        with episode_store(os.environ['TEST_DATABASE_URL'],'eval_baseline_fix') as store:
            seed_fixture(store,task.fixture)
            controller=baseline_factory(store,_catalog_from_fixture(task.fixture),config,client=client)
            result=run_episode(task,controller,store,repeat=1,now=config.now,limits={
                'max_model_calls':12,'max_tool_calls':24,'max_clarifications':3,'timeout_seconds':45})
            assert result.status=='complete',(task.id,result.error)
            assert grade_state(task,result.final_state).passed,(task.id,grade_state(task,result.final_state).reasons)
            assert grade_order(task,result).passed,(task.id,grade_order(task,result).reasons)
            assert result.reply and result.turns==2
            assert len(client.responses.calls)==len(actions)
            if task.category=='corrections':
                assert result.tool_calls==2
                initial=next(x['reply'] for x in result.interactions if x['kind']=='reply')
                assert 'Original record' in initial and 'Corrected' in initial


def test_baseline_correction_handles_no_match_and_pending_selection():
    from nutrition_demo.agent import Settings
    from nutrition_eval.baseline import FixedWorkflowBaseline
    service=SpyService()
    responses=iter([
        Result(True,{'candidates':[{'id':'event-1'},{'id':'event-2'}]}),
        Result(True,{'candidates':[{'id':'event-2'}]}),
        Result(True,{'candidates':[]}),
    ])
    service.find_events=lambda query: next(responses)
    client=FakeClient(
        {'action':'correct_meal','arguments':{'query':{},'changes':{'meal':'breakfast'}},'reply':'Review.'},
        {'action':'correct_meal','arguments':{'query':{'event_id':'event-2'},'changes':{}},'reply':'Review.'},
        {'action':'correct_meal','arguments':{'query':{},'changes':{'meal':'dinner'}},'reply':'Review.'})
    baseline=FixedWorkflowBaseline(service,FakeWorkflow(),client,Settings())
    assert baseline.handle('Correct a meal.').data['action']=='ask_user'
    assert baseline.handle('event-2').ok
    assert ('preview_correction',{'event_id':'event-2','changes':{'meal':'breakfast'}}) in service.calls
    assert 'baseline_pending_correction' not in baseline.workflow.load()
    before=sum(n=='preview_correction' for n,args in service.calls)
    empty=baseline.handle('Correct a nonexistent meal.')
    assert 'No matching meal record' in empty.data['message']
    assert sum(n=='preview_correction' for n,args in service.calls)==before


def test_baseline_correction_respects_tool_budget_and_does_not_autoconfirm():
    from nutrition_demo.agent import Settings
    from nutrition_eval.baseline import FixedWorkflowBaseline
    service=SpyService()
    service.find_events=lambda query: Result(True,{'candidates':[{'id':'event-1'}]})
    client=FakeClient({'action':'correct_meal','arguments':{'query':{},'changes':{'meal':'breakfast'}},'reply':'Review.'})
    workflow=FakeWorkflow()
    result=FixedWorkflowBaseline(service,workflow,client,Settings(max_tool_calls=1)).handle('Correct the meal.')
    assert not result.ok and result.data['counts']['tool_calls']==1
    assert not any(n=='preview_correction' for n,args in service.calls)
    assert workflow.commands==[]
