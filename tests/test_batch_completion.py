"""Offline completion-contract regressions; only the model boundary is faked."""
from copy import deepcopy
from decimal import Decimal
import json
from types import SimpleNamespace
import pytest


def set_targets(service, kcal='200'):
    assert service.set_profile({
        'timezone':'America/Los_Angeles',
        'meal_targets':{'kcal':kcal,'protein_g':'12.5','carbs_g':'25','fat_g':'2.5'},
        'daily_targets':{'kcal':'1800','protein_g':'120','carbs_g':'195','fat_g':'60'},
    }).ok


@pytest.mark.parametrize('message', [
    'Does the meal batch meet my meal targets?',
    'Compare the meal batch against the nutrient targets.',
    'List the allowed upper and lower bounds for the meal batch and compare each.',
])
def test_explicit_batch_comparison_captures_fixed_requirements(message):
    from nutrition_demo.completion import BatchTargetCompletion
    contract=BatchTargetCompletion.from_message(message,[{'id':'b1','name':'meal'}])
    assert contract is not None
    assert contract.request.batch_id == 'b1'
    assert contract.request.basis == 'per_box'
    assert contract.request.target_scope == 'meal'
    with pytest.raises(AttributeError):
        contract.request.target_scope='daily'


@pytest.mark.parametrize('message', [
    'How many boxes remain in the meal batch?',
    'What are my meal and daily targets?',
    'If the meal batch had 569.9 kcal, would it meet the targets?',
    'The meal batch has 569.9 kcal. Does it meet the targets?',
    'Preview preparation of a batch that meets the targets.',
    'Does the meal batch meet targets? Record one for lunch.',
    'Compare both batches against their targets.',
    'Does the meal batch with default addons meet its targets?',
])
def test_other_requests_do_not_activate_completion(message):
    from nutrition_demo.completion import BatchTargetCompletion
    assert BatchTargetCompletion.from_message(message,[{'id':'b1','name':'meal'}]) is None


def test_duplicate_batch_names_remain_ambiguous_and_ids_can_identify_requests():
    from nutrition_demo.completion import BatchTargetCompletion
    batches=[{'id':'b1','name':'curry batch'},{'id':'b2','name':'curry batch'}]
    contract=BatchTargetCompletion.from_message('Does the curry batch meet meal targets?',batches)
    assert contract is not None and contract.request.batch_id is None
    contract=BatchTargetCompletion.from_message('Does b1 meet my meal targets?',batches)
    assert contract is not None and contract.request.batch_id=='b1'
    contract=BatchTargetCompletion.from_message('Does curry batch (b1) meet meal targets?',batches)
    assert contract is not None and contract.request.batch_id=='b1'


@pytest.mark.parametrize('message', [
    'Does the entire meal batch meet targets?',
    'Does the meal batch total meet targets?',
    'Would the meal batch meet targets with different quantities?',
    'Does half a box of the meal batch meet my meal targets?',
    'Do two boxes of the meal batch meet my meal targets?',
    'Do 1.5 boxes of the meal batch meet my meal targets?',
    'Do 10 boxes of the meal batch meet my meal targets?',
])
def test_non_per_box_basis_is_out_of_scope(message):
    from nutrition_demo.completion import BatchTargetCompletion
    assert BatchTargetCompletion.from_message(message,[{'id':'b1','name':'meal'}]) is None


def test_conflicting_batch_name_and_id_require_clarification():
    from nutrition_demo.completion import BatchTargetCompletion
    batches=[{'id':'b1','name':'lunch batch'},{'id':'b2','name':'dinner batch'}]
    contract=BatchTargetCompletion.from_message('Does lunch batch (b2) meet meal targets?',batches)
    assert contract is not None and contract.request.batch_id is None
    assert set(contract.request.candidate_ids)=={'b1','b2'}


def test_overlapping_names_do_not_disable_the_contract():
    from nutrition_demo.completion import BatchTargetCompletion
    batches=[{'id':'b1','name':'meal'},{'id':'b2','name':'chicken meal'}]
    contract=BatchTargetCompletion.from_message('Does the chicken meal batch meet meal targets?',batches)
    assert contract is not None
    assert contract.request.batch_id=='b2'


def test_assessment_uses_current_targets_and_preserves_business_state(prepared):
    from nutrition_eval.state import read_business_state
    service,batch=prepared
    set_targets(service,'600')
    before=read_business_state(service.store)
    result=service.assess_batch_targets(batch)
    assert result.ok,result
    answer=result.data['comparison']
    assert answer['batch_id']==batch
    assert answer['basis']=='per_box' and answer['target_scope']=='meal'
    assert answer['metrics']['kcal']['actual']==Decimal('200')
    assert answer['metrics']['kcal']['target']==Decimal('600')
    assert answer['metrics']['kcal']['lower']==Decimal('570')
    assert answer['metrics']['kcal']['difference']==Decimal('-400')
    assert not answer['passed']
    assert read_business_state(service.store)==before


def test_contract_rejects_unknown_incomplete_and_cross_request_evidence(prepared):
    from nutrition_demo.completion import BatchTargetCompletion
    service,batch=prepared
    set_targets(service)
    batches=service.batch_summary().data['batches']
    contract=BatchTargetCompletion.from_message('Does the meal batch meet targets?',batches)
    assert not contract.finish('lookup-only',service).ok
    assessed=contract.assess(batch,service)
    assert assessed.ok
    answer_id=assessed.data['answer_id']
    other=BatchTargetCompletion.from_message('Does the meal batch meet targets?',batches)
    assert not other.finish(answer_id,service).ok
    # Even incomplete service evidence must never become a successful answer.
    del contract.artifacts[answer_id]['comparison']['metrics']['fat_g']
    assert not contract.finish(answer_id,service).ok


def test_contract_rejects_wrong_batch_and_stale_evidence(prepared):
    from nutrition_demo.completion import BatchTargetCompletion
    service,batch=prepared
    set_targets(service)
    contract=BatchTargetCompletion.from_message('Does the meal batch meet targets?',service.batch_summary().data['batches'])
    assert not contract.assess('another-batch',service).ok
    assessment=contract.assess(batch,service)
    set_targets(service,'600')
    assert not contract.finish(assessment.data['answer_id'],service).ok
    assessment=contract.assess(batch,service)
    assert contract.finish(assessment.data['answer_id'],service).ok
    assert contract.status=='answered'


def test_ambiguous_request_requires_external_selection():
    from nutrition_demo.completion import BatchTargetCompletion
    batches=[{'id':'b1','name':'curry lunch batch'},{'id':'b2','name':'curry dinner batch'}]
    contract=BatchTargetCompletion.from_message('Does my curry batch meet meal targets?',batches)
    assert contract.request.batch_id is None
    resumed=BatchTargetCompletion.from_message('Curry lunch batch.',batches,pending=contract.pending())
    assert resumed.request.batch_id=='b1'
    assert BatchTargetCompletion.from_message('Show inventory.',batches,pending=contract.pending()) is None


def test_assessment_requires_profile_targets(prepared):
    service,batch=prepared
    result=service.assess_batch_targets(batch)
    assert not result.ok and 'target' in result.error.lower()


def test_contract_accepts_depleted_batch_and_exact_boundary(prepared):
    from nutrition_demo.completion import BatchTargetCompletion
    from nutrition_demo.store import jsonb
    service,batch=prepared
    set_targets(service,'600')
    with service.store.transaction(lock=True) as c:
        c.execute('UPDATE batches SET remaining_boxes=0, data=data || %s WHERE id=%s',
                  (jsonb({'box_nutrients':{'kcal':'570','protein_g':'12.5','carbs_g':'25','fat_g':'2.5'}}),batch))
    contract=BatchTargetCompletion.from_message('Does the meal batch meet targets?',service.batch_summary().data['batches'])
    assessment=contract.assess(batch,service)
    assert assessment.ok
    assert contract.finish(assessment.data['answer_id'],service).ok
    assert contract.answer['passed']
    with service.store.transaction(lock=True) as c:
        c.execute('UPDATE batches SET data=data || %s WHERE id=%s',
                  (jsonb({'box_nutrients':{'kcal':'569.9','protein_g':'12.5','carbs_g':'25','fat_g':'2.5'}}),batch))
    contract=BatchTargetCompletion.from_message('Does the meal batch meet targets?',service.batch_summary().data['batches'])
    assessment=contract.assess(batch,service)
    assert contract.finish(assessment.data['answer_id'],service).ok
    assert not contract.answer['passed']


class ScriptedModel:
    """Fake only model I/O; tools, workflow, database and rendering remain real."""
    def __init__(self, steps):
        self.steps=iter(steps)
        self.requests=[]

    def create(self, **request):
        self.requests.append(deepcopy(request))
        actions=next(self.steps, [])
        if callable(actions):
            actions=actions(request)
        output=[SimpleNamespace(type='function_call',name=name,arguments=json.dumps(args),
                                call_id=f'call-{len(self.requests)}-{i}')
                for i,(name,args) in enumerate(actions)]
        return SimpleNamespace(output=output,status='completed',model='offline-model',usage=None,
                               output_text='All targets pass. This unchecked claim must never be displayed.')


def finish_latest(request):
    for item in reversed(request['input']):
        if item.get('type')=='function_call_output':
            data=json.loads(item['output']).get('data',{})
            if 'answer_id' in data:
                return [('finish_answer',{'answer_id':data['answer_id']})]
    raise AssertionError('The real assessment did not return answer evidence')


def make_agent(service, steps, **limits):
    from nutrition_demo.agent import DemoAgent, Settings
    from nutrition_demo.workflow import Workflow
    model=ScriptedModel(steps)
    return DemoAgent(service,Workflow(service),SimpleNamespace(responses=model),Settings(**limits))


def test_react_recovers_from_early_stop_and_lookup_only_finish(prepared):
    service,batch=prepared
    set_targets(service)
    agent=make_agent(service,[
        [('find_batches',{'query':'meal'})], [],
        [('finish_answer',{'answer_id':batch})],
        [('assess_batch_targets',{'batch_id':batch})], finish_latest,
    ])
    result=agent.handle('Does the meal batch meet meal targets? List all four actuals and targets.')
    assert result.ok,result
    assert result.data['completion_status']=='answered'
    assert result.data['counts']['model_calls']==5
    assert result.data['batch_target_answer']['passed']
    assert service.store.info()['counts']['events']==0


def test_react_rejects_wrong_batch_then_accepts_requested_evidence(prepared):
    service,batch=prepared
    set_targets(service)
    agent=make_agent(service,[
        [('assess_batch_targets',{'batch_id':'wrong-batch'})],
        [('assess_batch_targets',{'batch_id':batch})], finish_latest,
    ])
    result=agent.handle('Does the meal batch meet meal targets?')
    assert result.ok and result.data['completion_status']=='answered'
    assert result.data['batch_target_answer']['batch_id']==batch


def test_no_tool_exits_are_bounded_and_not_reported_as_answers(prepared):
    from nutrition_demo.display import render
    service,_=prepared
    set_targets(service)
    agent=make_agent(service,[])
    result=agent.handle('Does the meal batch meet meal targets?')
    assert not result.ok
    assert result.data['completion_status']=='incomplete'
    assert result.data['counts']['model_calls']==3
    assert 'comparison' in render(result).lower()
    assert 'unchecked claim' not in render(result)
    assert 'batch_target_answer' not in result.data


@pytest.mark.parametrize('limits', [{'max_model_calls':1},{'max_tool_calls':1}])
def test_resource_limits_cannot_turn_assessment_into_completion(prepared,limits):
    service,batch=prepared
    set_targets(service)
    agent=make_agent(service,[[('assess_batch_targets',{'batch_id':batch})],finish_latest],**limits)
    result=agent.handle('Does the meal batch meet meal targets?')
    assert not result.ok
    assert result.data['completion_status']=='incomplete'
    assert 'batch_target_answer' not in result.data


def test_read_only_contract_rejects_writes_and_unnecessary_clarification(prepared):
    service,batch=prepared
    set_targets(service)
    agent=make_agent(service,[
        [('preview_batch_addons',{'batch_id':batch,'items':[]})],
        [('ask_user',{'topic':'quantity'})],
        [('assess_batch_targets',{'batch_id':batch})],finish_latest,
    ])
    before=service.store.info()['counts']
    result=agent.handle('Does the meal batch meet meal targets?')
    assert result.ok and result.data['completion_status']=='answered'
    after=service.store.info()['counts']
    for table in ('events','previews','batch_addons','inventory_movements','operations'):
        assert after[table]==before[table]


def test_batch_clarification_resumes_comparison_without_guessing(prepared):
    service,batch=prepared
    set_targets(service)
    with service.store.transaction(lock=True) as c:
        c.execute('INSERT INTO batches SELECT %s,cooking_run_id,%s,total_boxes,remaining_boxes,data FROM batches WHERE id=%s',
                  ('other-batch','other',batch))
    agent=make_agent(service,[
        [('assess_batch_targets',{'batch_id':batch})],
        [('ask_user',{'topic':'batch'})],
    ])
    result=agent.handle('Does my curry batch meet meal targets?')
    assert result.ok and result.data['completion_status']=='awaiting_user'
    assert 'compare' in result.data['message']
    agent.client.responses=ScriptedModel([[('assess_batch_targets',{'batch_id':batch})],finish_latest])
    result=agent.handle('meal')
    assert result.ok and result.data['completion_status']=='answered'
    assert result.data['batch_target_answer']['batch_id']==batch
    assert not agent.workflow.load().get('pending_batch_comparison')


def test_missing_targets_pause_without_fabricating_comparison(prepared):
    service,batch=prepared
    agent=make_agent(service,[
        [('assess_batch_targets',{'batch_id':batch})],
        [('ask_user',{'topic':'profile'})],
    ])
    result=agent.handle('Does the meal batch meet meal targets?')
    assert result.ok and result.data['completion_status']=='awaiting_user'
    assert 'batch_target_answer' not in result.data


def test_new_plan_clears_pending_comparison(prepared):
    service,batch=prepared
    agent=make_agent(service,[[('ask_user',{'topic':'batch'})]])
    assert agent.handle('Does my curry batch meet meal targets?').data['completion_status']=='awaiting_user'
    assert agent.workflow.load().get('pending_batch_comparison')
    assert agent.handle('/new-plan').ok
    assert not agent.workflow.load().get('pending_batch_comparison')
    agent.client.responses=ScriptedModel([])
    result=agent.handle('meal')
    assert 'completion_status' not in result.data


def test_unrelated_request_keeps_existing_behavior_and_tool_registry(prepared):
    from nutrition_demo.tools import SCHEMAS
    service,_=prepared
    agent=make_agent(service,[[('list_inventory',{})],[]])
    result=agent.handle('Show inventory.')
    assert result.ok and 'completion_status' not in result.data
    assert 'assess_batch_targets' not in SCHEMAS and 'finish_answer' not in SCHEMAS
    assert not agent.workflow.load().get('pending_batch_comparison')


@pytest.mark.parametrize('kcal,overall,calorie_line', [
    ('200','Pass','Calories: Actual 200 kcal | Target 200 kcal | Allowed 190–210 kcal | Difference 0 kcal | Pass'),
    ('600','Fail','Calories: Actual 200 kcal | Target 600 kcal | Allowed 570–630 kcal | Difference -400 kcal | Fail'),
])
def test_completed_answer_renders_every_required_comparison(prepared,kcal,overall,calorie_line):
    from nutrition_demo.display import render
    service,batch=prepared
    set_targets(service,kcal)
    agent=make_agent(service,[[('assess_batch_targets',{'batch_id':batch})],finish_latest])
    result=agent.handle('Does the meal batch meet meal targets?')
    assert result.ok,result
    text=render(result)
    assert 'meal | Per-box comparison against configured meal targets.' in text
    assert calorie_line in text
    assert 'Protein: Actual 12.5 g | Target 12.5 g | Allowed 12.5–13.75 g | Difference 0 g | Pass' in text
    assert 'Carbohydrates: Actual 25 g | Target 25 g | Allowed 22.5–27.5 g | Difference 0 g | Pass' in text
    assert 'Fat: Actual 2.5 g | Target 2.5 g | Allowed 2.25–2.75 g | Difference 0 g | Pass' in text
    assert 'Overall meal-target status: '+overall in text
    assert 'Source status: synthetic' in text
    assert 'unchecked claim' not in text


def test_unfinished_assessment_does_not_display_an_answer(prepared):
    from nutrition_demo.display import render
    service,batch=prepared
    set_targets(service)
    agent=make_agent(service,[[('assess_batch_targets',{'batch_id':batch})]])
    result=agent.handle('Does the meal batch meet meal targets?')
    assert not result.ok and result.data['completion_status']=='incomplete'
    assert 'Overall meal-target status:' not in render(result)


def test_comparison_display_preserves_exact_values(prepared):
    from nutrition_demo.display import render
    from nutrition_demo.store import jsonb
    service,batch=prepared
    set_targets(service,'600')
    with service.store.transaction(lock=True) as c:
        c.execute('UPDATE batches SET data=data || %s WHERE id=%s',
                  (jsonb({'box_nutrients':{'kcal':'569.999','protein_g':'12.5','carbs_g':'25','fat_g':'2.5'}}),batch))
    agent=make_agent(service,[[('assess_batch_targets',{'batch_id':batch})],finish_latest])
    text=render(agent.handle('Does the meal batch meet meal targets?'))
    assert 'Actual 569.999 kcal | Target 600 kcal | Allowed 570–630 kcal | Difference -30.001 kcal | Fail' in text
