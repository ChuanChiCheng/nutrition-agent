"""Offline executable fixture; uses the same workflow, schemas and services as live chat."""
from datetime import datetime,timezone
import json
from pathlib import Path
from types import SimpleNamespace
from .agent import DemoAgent,Settings
from .catalog import Catalog,DATA_DIR
from .models import encode
from .service import NutritionService
from .workflow import Workflow


def load_scenario():
    return json.loads((DATA_DIR/'scenario.json').read_text())


class ScriptedResponses:
    def __init__(self):self.next_call=None;self.counter=0
    def create(self,**kwargs):
        self.counter+=1
        output=[]
        if self.next_call:
            name,args=self.next_call;self.next_call=None
            output=[SimpleNamespace(type='function_call',name=name,arguments=json.dumps(args),call_id='offline_'+str(self.counter))]
        return SimpleNamespace(output=output,usage=None,output_text='')


def run_scripted(store):
    scenario=load_scenario();catalog=Catalog(scenario['catalog'])
    counts=store.info()['counts']
    if any(counts[t] for t in ('cooking_runs','events','workflow_sessions','agent_runs')):
        raise ValueError('Scripted scenario requires a fresh isolated seed; use a new Compose project')
    service=NutritionService(store,catalog,clock=lambda:datetime(2026,11,18,7,30,tzinfo=timezone.utc))
    inventory={i['ingredient_id']:str(i['quantity']) for i in service.list_inventory().data['items']}
    if inventory!={'fixture_mix':'1000','fixture_yogurt':'10'}:
        raise ValueError('Scripted scenario requires its exact synthetic fixture, never personal data')
    responses=ScriptedResponses()
    agent=DemoAgent(service,Workflow(service,'scripted'),SimpleNamespace(responses=responses),Settings(model='scripted-offline',reasoning_effort=None))
    steps=[]
    def checked(result):
        if not result.ok:raise ValueError('Scripted step failed: '+str(result.error))
        return result.data
    def call(name,args):
        responses.next_call=(name,args)
        message='I ate one box from '+args['batch_id'] if name=='log_meal' else 'Synthetic scenario: '+name
        r=checked(agent.handle(message))
        if not r['tool_results'] or not r['tool_results'][0]['result']['ok']:
            raise ValueError('Scripted tool step failed')
        return r
    agent.handle('/new-plan');checked(agent.handle('/inventory-ok'));steps.append('inventory_confirmed')
    checked(agent.handle('/select curry'));steps.append('recipe_selected')
    item=lambda qty:{'ingredient_id':'fixture_mix','quantity':str(qty),'unit':'g','state':'synthetic'}
    r=call('propose_recipe',{'items':[item(600)],'boxes':6});steps.append('proposal_calculated')
    checked(agent.handle('/accept-recipe '+r['proposal']['id']));steps.append('recipe_accepted')
    r=call('preview_preparation',{'recipe_id':'curry','actual_usage':[item(800)],'outputs':[
        {'name':'Synthetic eight-box batch','boxes':8,'allocations':[{'cooking_ingredient_id':'fixture_mix','quantity':'800','unit':'g'}]}],
        'prepared_on':'2026-11-17','confirmed_dispositions':[]})
    prepared=checked(agent.handle('/confirm '+r['pending_preview']));batch=prepared['batch_ids'][0];steps.append('preparation_confirmed')
    r=call('preview_batch_addons',{'batch_id':batch,'items':[{'ingredient_id':'fixture_yogurt','quantity':'1','unit':'serving','state':'synthetic'}]})
    checked(agent.handle('/confirm '+r['pending_preview']));steps.append('addons_confirmed')
    r=call('log_meal',{'batch_id':batch,'eaten_on':'today','meal':'dinner','addon_override':None})
    event=r['tool_results'][0]['result']['data']['event_id'];steps.append('meal_recorded')
    r=call('preview_correction',{'event_id':event,'changes':{'date':'yesterday'}})
    checked(agent.handle('/confirm '+r['pending_preview']));steps.append('date_corrected')
    batch=service.batch_summary().data['batches'][0]
    return encode({'synthetic':True,'live_model_used':False,'planned_boxes':6,'actual_boxes':8,'remaining_boxes':batch['remaining_boxes'],
                   'inventory':{i['ingredient_id']:str(i['quantity']) for i in service.list_inventory().data['items']},
                   'corrected_summary':service.daily_summary('yesterday').data,'trace_steps':steps})
