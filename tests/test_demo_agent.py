import json
from types import SimpleNamespace
from decimal import Decimal as D
import pytest
from nutrition_demo.models import Result


class Responses:
    def __init__(self,steps):self.steps=iter(steps);self.inputs=[]
    def create(self,**kwargs):
        self.inputs.append(kwargs)
        step=next(self.steps)
        if isinstance(step,Exception):raise step
        output=[]
        for i,(name,args) in enumerate(step):
            output.append(SimpleNamespace(type='function_call',name=name,arguments=json.dumps(args),call_id=f'call_{len(self.inputs)}_{i}',
                model_dump=lambda:None))
        return SimpleNamespace(id='response_'+str(len(self.inputs)),output=output,output_text='已達標且全部完成；我已自行核准。',
                               usage=SimpleNamespace(input_tokens=100,output_tokens=50,total_tokens=150))


def agent(service,steps,settings=None):
    from nutrition_demo.agent import DemoAgent,Settings
    from nutrition_demo.workflow import Workflow
    return DemoAgent(service,Workflow(service),SimpleNamespace(responses=Responses(steps)),settings or Settings())


def profile(s):
    assert s.set_profile({'timezone':'America/Los_Angeles','meal_targets':{'kcal':200,'protein_g':'12.5','carbs_g':25,'fat_g':'2.5'},
                         'daily_targets':{'kcal':1800,'protein_g':120,'carbs_g':195,'fat_g':60}}).ok


def proposal_items():
    return [{'ingredient_id':'chicken','quantity':800,'unit':'g','state':'raw'},
            {'ingredient_id':'rice','quantity':400,'unit':'g','state':'dry'}]


def test_model_priority(monkeypatch):
    from nutrition_demo.agent import Settings
    monkeypatch.delenv('OPENAI_MODEL',raising=False)
    assert Settings.from_env().model=='gpt-6-luna'
    monkeypatch.setenv('OPENAI_MODEL','other')
    assert Settings.from_env().model=='other'
    assert Settings.from_env('cli').model=='cli'


def test_choose_before_customize_and_confirm_recipe(stocked):
    profile(stocked)
    a=agent(stocked,[[('propose_recipe',{'items':proposal_items(),'boxes':8})],[]])
    r=a.handle('幫我規劃')
    assert r.ok
    assert not r.data['tool_results'][0]['result']['ok']
    assert a.handle('/inventory-ok').ok
    assert a.handle('/select curry').ok
    a.client.responses=Responses([[('propose_recipe',{'items':proposal_items(),'boxes':8})],[]])
    r=a.handle('客製化八盒')
    assert r.data['proposal']['calculation']['targets']['passed'] is True
    assert r.data['stage']=='recipe_confirmation'
    pid=r.data['proposal']['id']
    assert a.handle('/accept-recipe '+pid).ok
    assert a.workflow.load()['stage']=='cooking'
    assert stocked.store.info()['counts']['cooking_runs']==0


def test_invalid_proposal_then_retry_and_limit(stocked):
    profile(stocked)
    a=agent(stocked,[]);a.handle('/inventory-ok');a.handle('/select curry')
    a.client.responses=Responses([[('propose_recipe',{'items':[],'boxes':6})],
                                  [('propose_recipe',{'items':proposal_items(),'boxes':8})],[]])
    r=a.handle('調整')
    assert r.data['proposal']['calculation']['targets']['passed']
    assert len(r.data['tool_results'])==2
    # A failed target remains visible after max attempts and requires explicit outside acceptance.
    a.handle('/select curry')
    bad=[{'ingredient_id':'chicken','quantity':100,'unit':'g','state':'raw'}]
    a.client.responses=Responses([[('propose_recipe',{'items':bad,'boxes':1})]]*4+[[]])
    r=a.handle('再試')
    assert r.data['proposal']['calculation']['targets']['passed'] is False
    assert r.data['stage']=='customization_limit'
    assert not a.handle('/accept-recipe '+r.data['proposal']['id']).ok
    assert a.handle('/accept-recipe '+r.data['proposal']['id']+' outside').ok
    assert a.workflow.load()['proposal']['calculation']['targets']['passed'] is False


def test_unknown_tool_illegal_args_and_forged_approval(prepared):
    s,b=prepared
    a=agent(s,[[('confirm_preview',{'preview_id':'fake','request_id':'bot'})],
               [('log_meal',{'batch_id':b,'eaten_on':'today','meal':None,'addon_override':[],'request_id':'injected'})],[]])
    r=a.handle('查詢')
    assert r.ok
    assert all(not x['result']['ok'] for x in r.data['tool_results'])
    assert s.store.info()['counts']['events']==0
    assert '已達標' not in r.data['message']


def test_direct_meal_query_and_correction_routes(prepared):
    s,b=prepared
    a=agent(s,[[('log_meal',{'batch_id':b,'eaten_on':'today','meal':'lunch','addon_override':None})],[]])
    r=a.handle('吃了一盒')
    assert r.data['tool_results'][0]['result']['ok']
    assert s.store.info()['counts']['events']==1
    e=r.data['tool_results'][0]['result']['data']['event_id']
    a.client.responses=Responses([[('preview_correction',{'event_id':e,'changes':{'date':'yesterday'}})],[]])
    r=a.handle('改成昨天')
    pid=r.data['pending_preview']
    assert s.daily_summary('today').data['events']==1
    assert a.handle('/confirm '+pid).ok
    assert s.daily_summary('yesterday').data['events']==1


def test_workflow_reopens_and_persists_clarification(stocked):
    from nutrition_demo.workflow import Workflow
    a=agent(stocked,[[('ask_user',{'topic':'batch'})],[]])
    assert a.handle('我吃了').ok
    assert Workflow(stocked).load()['waiting_question']=='請選擇批次'
    other=agent(stocked,[])
    assert other.workflow.load()['waiting_question']=='請選擇批次'


def test_limits_and_api_failure_do_not_write(stocked):
    from nutrition_demo.agent import Settings
    a=agent(stocked,[[('list_inventory',{})]]*4,Settings(max_model_calls=2,max_tool_calls=1))
    r=a.handle('查詢')
    assert r.data['limit_reached']
    assert r.data['counts']['tool_calls']==1
    assert stocked.store.info()['counts']['events']==0
    a=agent(stocked,[RuntimeError('secret-from-upstream')])
    r=a.handle('查詢')
    assert not r.ok
    assert 'secret' not in str(r)


def test_run_trace_records_actual_model_and_parameters(stocked):
    from nutrition_demo.agent import Settings
    a=agent(stocked,[[('list_inventory',{})],[]],Settings(model='gpt-6-luna',reasoning_effort='medium'))
    r=a.handle('查看庫存')
    with stocked.store.transaction() as c:
        run=c.execute('SELECT settings,trace FROM agent_runs WHERE id=%s',(r.data['run_id'],)).fetchone()
    assert run['settings']['model']=='gpt-6-luna'
    assert run['settings']['reasoning_effort']=='medium'
    assert run['trace'][-1]['usage']['total_tokens']==150


def test_incompatible_model_parameters_clear_error():
    from nutrition_demo.agent import Settings
    with pytest.raises(ValueError,match='reasoning'):
        Settings(model='unknown-model',reasoning_effort='medium')


def test_profile_model_tool_requires_user_confirmation(service):
    values={'timezone':'America/Los_Angeles','meal_targets':{'kcal':600,'protein_g':40,'carbs_g':65,'fat_g':20},
            'daily_targets':{'kcal':1800,'protein_g':120,'carbs_g':195,'fat_g':60},'equipment':[],'container_ml':1000}
    a=agent(service,[[('preview_profile',{'values':values})],[]])
    r=a.handle('設定我的目標')
    assert service.get_profile().data.get('needs_setup') is True
    assert a.handle('/confirm '+r.data['pending_preview']).ok
    assert service.get_profile().data['daily_targets']['kcal']=='1800'


def test_repeated_tool_call_cannot_record_same_meal_twice(prepared):
    s,b=prepared
    args={'batch_id':b,'eaten_on':'today','meal':'lunch','addon_override':None}
    a=agent(s,[[('log_meal',args)],[('log_meal',args)],[]])
    r=a.handle('我吃了一盒午餐')
    assert r.ok
    assert s.store.info()['counts']['events']==1
    assert s.batch_summary().data['batches'][0]['remaining_boxes']==7


def test_followup_clears_previous_question(prepared):
    s,b=prepared
    a=agent(s,[[('ask_user',{'topic':'batch'})]])
    a.handle('吃了一盒')
    a.client.responses=Responses([[('log_meal',{'batch_id':b,'eaten_on':'today','meal':None,'addon_override':None})],[]])
    r=a.handle('是這個批次 '+b)
    assert r.data['waiting_question'] is None


def test_trace_uses_returned_model_identity_and_incomplete_is_reported(stocked):
    from nutrition_demo.agent import DemoAgent,Settings
    from nutrition_demo.workflow import Workflow
    class ActualResponse:
        def create(self,**kwargs):
            return SimpleNamespace(output=[],usage=None,model='gpt-6-luna-exact-snapshot',status='incomplete',
                                   incomplete_details=SimpleNamespace(reason='max_output_tokens'),output_text='')
    a=DemoAgent(stocked,Workflow(stocked),SimpleNamespace(responses=ActualResponse()),Settings())
    r=a.handle('查詢')
    assert not r.ok and 'incomplete' in r.error
    with stocked.store.transaction() as c:
        trace=c.execute('SELECT trace FROM agent_runs WHERE id=%s',(r.data['run_id'],)).fetchone()['trace']
    assert trace[0]['model']=='gpt-6-luna-exact-snapshot'
    assert trace[0]['requested_model']=='gpt-6-luna'


def test_ui_confirmation_retry_recovers_completed_result_after_other_write(prepared):
    s,b=prepared
    a=agent(s,[[('preview_batch_addons',{'batch_id':b,'items':[]})]])
    r=a.handle('確認此批次不加餐')
    pid=r.data['pending_preview']
    first=a.handle('/confirm '+pid)
    assert first.ok
    assert s.log_meal(b,'today',None,'other-write').ok
    assert a.handle('/confirm '+pid)==first


def test_persisted_pending_preview_can_be_redisplayed(prepared):
    s,b=prepared
    a=agent(s,[[('preview_batch_addons',{'batch_id':b,'items':[]})]])
    r=a.handle('不要加餐')
    other=agent(s,[])
    preview=other.handle('/preview')
    assert preview.ok
    assert preview.data['id']==r.data['pending_preview']
    assert preview.data['kind']=='addons' and 'changes' in preview.data


def test_valid_meal_tool_during_query_cannot_consume(prepared):
    s,b=prepared
    a=agent(s,[[('log_meal',{'batch_id':b,'eaten_on':'today','meal':None,'addon_override':None})],[]])
    r=a.handle('這個批次每盒有多少熱量？')
    assert r.ok and not r.data['tool_results'][0]['result']['ok']
    assert s.store.info()['counts']['events']==0


def test_meal_tool_respects_explicit_request_not_to_record(prepared):
    s,b=prepared
    a=agent(s,[[('log_meal',{'batch_id':b,'eaten_on':'today','meal':None,'addon_override':None})],[]])
    r=a.handle('我吃了一盒午餐，但不要記錄')
    assert r.ok and not r.data['tool_results'][0]['result']['ok']
    assert s.store.info()['counts']['events']==0


def test_api_failure_after_meal_retyping_request_recovers_instead_of_consuming_twice(prepared):
    s,b=prepared;message='我今天午餐吃了一盒 '+b
    args={'batch_id':b,'eaten_on':'today','meal':'lunch','addon_override':None}
    a=agent(s,[[('log_meal',args)],RuntimeError('network interrupted')])
    first=a.handle(message)
    assert not first.ok and s.store.info()['counts']['events']==1
    other=agent(s,[[('log_meal',args)],[]])
    retry=other.handle(message)
    assert retry.ok and retry.data['recovered'] is True
    assert s.store.info()['counts']['events']==1
    assert s.batch_summary().data['batches'][0]['remaining_boxes']==7
    other.client.responses=Responses([[('log_meal',args)],[]])
    next_meal=other.handle(message)
    assert next_meal.ok and not next_meal.data.get('recovered')
    assert s.store.info()['counts']['events']==2
    assert s.batch_summary().data['batches'][0]['remaining_boxes']==6


def test_same_meal_sentence_in_a_new_turn_is_a_new_meal(prepared):
    s,b=prepared;message='我今天午餐吃了一盒 '+b
    args={'batch_id':b,'eaten_on':'today','meal':'lunch','addon_override':None}
    a=agent(s,[[('log_meal',args)],[],[('log_meal',args)],[]])
    assert a.handle(message).ok
    second=a.handle(message)
    assert second.ok and not second.data.get('recovered')
    assert s.store.info()['counts']['events']==2
    assert s.batch_summary().data['batches'][0]['remaining_boxes']==6


def test_purchase_confirm_and_preparation_reject_resume_cooking(prepared):
    s,b=prepared
    a=agent(s,[])
    state=a.workflow.load();state.update(stage='cooking',accepted_recipe='accepted',selected_recipe='curry')
    a.workflow.save(state)
    a.client.responses=Responses([[('preview_inventory_change',{'items':[{'ingredient_id':'chicken','quantity':1,'unit':'g','state':'raw'}],'mode':'purchase'})]])
    r=a.handle('我買了雞胸一克，請預覽入庫')
    assert a.handle('/confirm '+r.data['pending_preview']).ok
    assert a.workflow.load()['stage']=='cooking'
    a.client.responses=Responses([[('preview_preparation',{'recipe_id':'curry','actual_usage':[{'ingredient_id':'chicken','quantity':100,'unit':'g','state':'raw'}],
        'outputs':[{'name':'actual','boxes':1,'allocations':[{'cooking_ingredient_id':'chicken','quantity':100,'unit':'g'}]}],'prepared_on':'today'})]])
    r=a.handle('做完了一盒，先預覽')
    assert a.handle('/reject '+r.data['pending_preview']).ok
    assert a.workflow.load()['stage']=='cooking'


def test_new_plan_cancels_previous_pending_preview(prepared):
    s,b=prepared
    a=agent(s,[[('preview_batch_addons',{'batch_id':b,'items':[]})]])
    p=a.handle('不要加餐').data['pending_preview']
    assert a.handle('/new-plan').ok
    assert a.workflow.load().get('pending_preview') is None
    assert not a.handle('/confirm '+p).ok
    assert not s.confirm_preview(p,'old-plan').ok


def test_question_tool_cannot_display_unverified_execution_claim(stocked):
    a=agent(stocked,[[('ask_user',{'topic':'details'})],[]])
    r=a.handle('幫我規劃')
    from nutrition_demo.display import render
    text=render(r)
    assert '已達標且我已自行核准' not in text
    assert '請補充這次操作缺少的實際資訊' in text


def test_grounded_question_specific_cooking_answer_uses_source_evidence(store,clock):
    from nutrition_demo.catalog import Catalog
    from nutrition_demo.service import NutritionService
    s=NutritionService(store,Catalog.load(),clock=clock)
    a=agent(s,[[('get_recipe',{'recipe_id':'curry'})],[('explain_cooking',{'recipe_id':'curry','evidence_ids':['source:2:summary']})],[]])
    r=a.handle('為什麼雞胸要後下？請只根據咖哩來源說明')
    from nutrition_demo.display import render
    text=render(r)
    assert '保留口感' in text and '來源' in text and '2' in text
    assert s.store.info()['counts']['events']==0


def test_log_trace_request_id_points_to_completed_operation(prepared):
    s,b=prepared
    a=agent(s,[[('log_meal',{'batch_id':b,'eaten_on':'today','meal':None,'addon_override':None})],[]])
    r=a.handle('我吃了一盒 '+b)
    with s.store.transaction() as c:
        trace=c.execute('SELECT trace FROM agent_runs WHERE id=%s',(r.data['run_id'],)).fetchone()['trace']
        tool=next(t for t in trace if t['type']=='tool' and t['name']=='log_meal')
        assert c.execute('SELECT 1 FROM operations WHERE request_id=%s',(tool['request_id'],)).fetchone()


def test_malformed_tool_arguments_do_not_inherit_previous_trace_arguments(store,clock):
    from nutrition_demo.catalog import Catalog
    from nutrition_demo.service import NutritionService
    from nutrition_demo.workflow import Workflow
    from nutrition_demo.agent import DemoAgent,Settings
    service=NutritionService(store,Catalog.load(),clock=clock)
    call=SimpleNamespace(type='function_call',name='list_inventory',arguments='{bad json',call_id='bad')
    response=SimpleNamespace(output=[call],usage=None,status='completed')
    client=SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs:response))
    result=DemoAgent(service,Workflow(service),client,Settings()).handle('查庫存')
    with store.transaction() as c:
        trace=c.execute('SELECT trace FROM agent_runs WHERE id=%s',(result.data['run_id'],)).fetchone()['trace']
    tool=next(entry for entry in trace if entry['type']=='tool')
    assert tool['arguments'] is None
    assert tool['result']['error']=='Malformed tool arguments'
