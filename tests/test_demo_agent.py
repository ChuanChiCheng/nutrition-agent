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
    a=agent(stocked,[[('ask_user',{'question':'請選擇批次'})],[]])
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
