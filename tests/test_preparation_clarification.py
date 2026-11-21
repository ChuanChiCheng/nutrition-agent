"""Preparation questions must correspond to missing facts or actual conflicts."""
from copy import deepcopy
from decimal import Decimal
import pytest


def accepted_state():
    return {
        'stage':'cooking','selected_recipe':'curry','accepted_recipe':'accepted-1',
        'proposal':{'id':'accepted-1','items':[
            {'ingredient_id':'chicken','quantity':'500','unit':'g','state':'raw'},
            {'ingredient_id':'rice','quantity':'250','unit':'g','state':'dry'},
            {'ingredient_id':'broccoli','quantity':'300','unit':'g','state':'raw'},
        ],'boxes':6},
    }


def supplied_details():
    return {
        'actual_usage':[
            {'ingredient_id':'chicken','quantity':'300','unit':'g','state':'raw'},
            {'ingredient_id':'rice','quantity':'150','unit':'g','state':'dry'},
        ],
        'outputs':[{'name':'curry','boxes':5,'allocations':[
            {'cooking_ingredient_id':'chicken','quantity':'300','unit':'g'},
            {'cooking_ingredient_id':'rice','quantity':'150','unit':'g'},
        ]}],
        'prepared_on':'2026-11-18',
    }


def draft_for(patch):
    from nutrition_demo.preparation import PreparationDraft
    draft=PreparationDraft(accepted_state())
    assert draft.update(patch).ok
    return draft


def test_known_amounts_produce_ingredient_omission_question(catalog):
    draft=draft_for(supplied_details())
    issues=draft.issues(catalog)
    assert [i['kind'] for i in issues]==['omission']
    assert issues[0]['ingredient_id']=='broccoli'
    assert 'accepted recipe includes broccoli' in issues[0]['question']
    assert 'Did you use any broccoli?' in issues[0]['question']
    assert 'Provide the actual quantity' not in issues[0]['question']


def test_partial_details_merge_without_losing_known_fields(catalog):
    draft=draft_for({'actual_usage':[{'ingredient_id':'chicken','unit':'g','state':'raw'}],
                     'prepared_on':'2026-11-18','outputs':[{'name':'curry','boxes':5}]})
    first=draft.issues(catalog)[0]
    assert first['kind']=='quantity' and first['ingredient_id']=='chicken'
    assert 'chicken' in first['question'] and 'g' in first['question']
    assert draft.update({'actual_usage':[{'ingredient_id':'chicken','quantity':'300'}]}).ok
    assert draft.data['actual_usage'][0]=={'ingredient_id':'chicken','quantity':'300','unit':'g','state':'raw'}
    assert draft.data['prepared_on']=='2026-11-18'
    assert draft.data['outputs'][0]['boxes']==5


@pytest.mark.parametrize('reply',['No.','No, I did not use any broccoli.'])
def test_omission_requires_external_answer_not_model_certification(catalog,reply):
    draft=draft_for(supplied_details())
    assert not draft.update({'omitted_ingredients':['broccoli']}).ok
    assert draft.ask('details',catalog).ok
    assert draft.apply_reply(reply).ok
    assert draft.issues(catalog)==[]
    assert draft.data['actual_usage']==supplied_details()['actual_usage']
    assert draft.data['prepared_on']=='2026-11-18'


def test_missing_actual_ingredients_can_be_asked_after_other_facts_are_captured(catalog):
    draft=draft_for({'outputs':[{'name':'curry','boxes':5}],'prepared_on':'2026-11-18'})
    assert draft.issues(catalog)[0]['kind']=='ingredients'
    question=draft.ask('details',catalog)
    assert question.ok and 'Which ingredients did you actually use?' in question.data['waiting_question']
    assert draft.data['outputs'][0]['boxes']==5


def test_unknown_ingredient_reply_replaces_only_pending_identity_and_retains_fields(catalog):
    from nutrition_demo.preparation import PreparationDraft
    details=complete_details()
    details['actual_usage'][0]['ingredient_id']='chickn'
    draft=draft_for(details)
    assert draft.issues(catalog)[0]['kind']=='ingredient'
    assert draft.ask('details',catalog).ok
    state=accepted_state()
    state['preparation_draft']=draft.saved()
    resumed=PreparationDraft.from_message('chicken',state)
    assert resumed is not None
    assert resumed.update({'actual_usage':[{'ingredient_id':'chicken'}]}).ok
    actual={item['ingredient_id']:item for item in resumed.data['actual_usage']}
    assert 'chickn' not in actual
    assert actual['chicken']=={'ingredient_id':'chicken','quantity':'300','unit':'g','state':'raw'}
    assert resumed.issues(catalog)==[]


def test_ingredient_denial_can_be_supplied_in_the_original_request(catalog):
    from nutrition_demo.preparation import PreparationDraft
    draft=PreparationDraft.from_message('Preview cooking five boxes; no broccoli was used.',accepted_state())
    assert draft.update(supplied_details()).ok
    assert draft.issues(catalog)==[]


@pytest.mark.parametrize('reply',['g.','grams'])
def test_short_unit_reply_resumes_the_pending_field(catalog,reply):
    from nutrition_demo.preparation import PreparationDraft
    details=complete_details()
    del details['actual_usage'][0]['unit']
    draft=draft_for(details)
    assert draft.ask('quantity',catalog).ok
    state=accepted_state()
    state['preparation_draft']=draft.saved()
    resumed=PreparationDraft.from_message(reply,state)
    assert resumed is not None
    assert resumed.data['actual_usage'][0]['quantity']=='300'


def test_unrelated_target_change_cannot_be_treated_as_a_quantity_reply(catalog):
    from nutrition_demo.preparation import PreparationDraft
    details=complete_details()
    del details['actual_usage'][0]['quantity']
    draft=draft_for(details)
    assert draft.ask('quantity',catalog).ok
    state=accepted_state()
    state['preparation_draft']=draft.saved()
    assert PreparationDraft.from_message('Set my daily targets to 2000 kcal.',state) is None


def test_negative_omission_answer_must_not_hide_mixed_actions(catalog):
    draft=draft_for(supplied_details())
    assert draft.ask('details',catalog).ok
    assert not draft.apply_reply('No, and record my lunch.').ok
    assert draft.issues(catalog)[0]['kind']=='omission'


def test_missing_split_allocation_is_not_inferred_from_boxes(catalog):
    details=supplied_details()
    details['actual_usage'].append({'ingredient_id':'broccoli','quantity':'300','unit':'g','state':'raw'})
    details['outputs']=[{'name':'lunch','boxes':3},{'name':'curry only','boxes':1}]
    draft=draft_for(details)
    issues=draft.issues(catalog)
    assert issues[0]['kind']=='allocations'
    assert 'lunch' in issues[0]['question']
    assert all('allocations' not in b for b in draft.data['outputs'])


def test_complete_draft_rejects_unnecessary_questions(catalog):
    details=supplied_details()
    details['actual_usage'].append({'ingredient_id':'broccoli','quantity':'300','unit':'g','state':'raw'})
    details['outputs'][0]['allocations'].append({'cooking_ingredient_id':'broccoli','quantity':'300','unit':'g'})
    draft=draft_for(details)
    assert draft.issues(catalog)==[]
    assert not draft.ask('quantity',catalog).ok


def test_conservation_conflict_is_a_specific_question(catalog):
    details=supplied_details()
    state=accepted_state()
    state['proposal']['items']=state['proposal']['items'][:2]
    from nutrition_demo.preparation import PreparationDraft
    draft=PreparationDraft(state)
    details['outputs'][0]['allocations'][0]['quantity']='250'
    assert draft.update(details).ok
    issue=draft.issues(catalog)[0]
    assert issue['kind']=='conservation'
    assert 'chicken' in issue['question'] and '50' in issue['question']
    assert not draft.payload(catalog).ok


def test_unit_and_state_conflicts_are_not_converted(catalog):
    details=supplied_details()
    details['actual_usage'][0]['state']='cooked'
    draft=draft_for(details)
    issue=draft.issues(catalog)[0]
    assert issue['kind']=='basis'
    assert 'chicken' in issue['question'] and 'raw' in issue['question']
    assert draft.data['actual_usage'][0]['state']=='cooked'


def test_stale_recipe_draft_is_not_resumed():
    from nutrition_demo.preparation import PreparationDraft
    state=accepted_state()
    draft=PreparationDraft(state)
    state['preparation_draft']=draft.saved()
    state['accepted_recipe']='accepted-2'
    assert PreparationDraft.from_message('No.',state) is None


@pytest.mark.parametrize('message',[
    'How do I cook this recipe?', 'Show inventory.',
    'Does the curry batch meet meal targets?',
    'How many calories were in my lunch on November 10?',
])
def test_other_requests_do_not_activate_preparation(message):
    from nutrition_demo.preparation import PreparationDraft
    assert PreparationDraft.from_message(message,accepted_state()) is None


@pytest.mark.parametrize('message',[
    'Preview cooking five boxes and record my lunch.',
    'Preview preparing five boxes and buy rice.',
    'Preview cooking five boxes and correct yesterday\'s dinner.',
])
def test_mixed_operations_do_not_enter_preparation_only_scope(message):
    from nutrition_demo.preparation import PreparationDraft
    assert PreparationDraft.from_message(message,accepted_state()) is None


def cooking_agent(service,steps):
    from test_batch_completion import make_agent,set_targets
    set_targets(service)
    agent=make_agent(service,steps)
    workflow=agent.workflow
    assert workflow.command('/inventory-ok').ok
    assert workflow.command('/select curry').ok
    proposal=workflow.propose(accepted_state()['proposal']['items'],6)
    assert proposal.ok,proposal
    assert workflow.command('/accept-recipe '+proposal.data['id']+' outside').ok
    return agent


PREVIEW_REQUEST='Preview preparing 5 boxes using 300 g raw chicken and 150 g dry rice on November 18; do not save without approval.'


def test_generic_question_is_replaced_by_justified_omission_question(stocked):
    from nutrition_demo.display import render
    agent=cooking_agent(stocked,[
        [('ask_user',{'topic':'quantity'})],
        [('update_preparation_draft',supplied_details())],
        [('ask_user',{'topic':'details'})],
    ])
    before=stocked.store.info()['counts']
    result=agent.handle(PREVIEW_REQUEST)
    assert result.ok,result
    assert result.data['preparation_status']=='awaiting_user'
    assert 'Did you use any broccoli?' in result.data['message']
    assert 'Provide the actual quantity, unit' not in render(result)
    draft=agent.workflow.load()['preparation_draft']['data']
    assert draft['actual_usage']==supplied_details()['actual_usage']
    assert draft['prepared_on']=='2026-11-18' and draft['outputs'][0]['boxes']==5
    assert stocked.store.info()['counts']['previews']==before['previews']


@pytest.mark.parametrize('outcome',['confirm','reject'])
def test_external_omission_reply_retains_facts_and_requires_approval(stocked,outcome):
    from test_batch_completion import ScriptedModel
    from test_demo_preparation import quantities
    agent=cooking_agent(stocked,[
        [('update_preparation_draft',supplied_details())],[('ask_user',{'topic':'details'})],
    ])
    assert agent.handle(PREVIEW_REQUEST).data['preparation_status']=='awaiting_user'
    before=quantities(stocked)
    agent.client.responses=ScriptedModel([[('preview_preparation',{})]])
    preview=agent.handle('No.')
    assert preview.ok,preview
    assert preview.data['preparation_status']=='awaiting_approval'
    preview_id=preview.data['pending_preview']
    assert quantities(stocked)==before and stocked.store.info()['counts']['cooking_runs']==0
    assert not stocked.confirm_preview(preview_id,'model-approval',actor='model').ok
    assert not agent.handle('/confirm wrong-id').ok
    assert agent.handle('/'+outcome+' '+preview_id).ok
    after=quantities(stocked)
    assert after['chicken']==(Decimal('700') if outcome=='confirm' else before['chicken'])
    assert after['rice']==(Decimal('850') if outcome=='confirm' else before['rice'])
    assert after['broccoli']==before['broccoli']
    assert stocked.store.info()['counts']['cooking_runs']==(1 if outcome=='confirm' else 0)


def complete_details():
    details=supplied_details()
    details['actual_usage'].append({'ingredient_id':'broccoli','quantity':'60','unit':'g','state':'raw'})
    details['outputs'][0]['allocations'].append({'cooking_ingredient_id':'broccoli','quantity':'60','unit':'g'})
    return details


def test_single_missing_quantity_reply_does_not_erase_known_fields(stocked):
    from test_batch_completion import ScriptedModel
    details=complete_details()
    del details['actual_usage'][0]['quantity']
    agent=cooking_agent(stocked,[[('update_preparation_draft',details)],[('ask_user',{'topic':'quantity'})]])
    question=agent.handle('Preview cooking these actual ingredients into five boxes.')
    assert question.ok and 'How much chicken' in question.data['message']
    assert ' in g?' in question.data['message']
    agent.client.responses=ScriptedModel([
        [('update_preparation_draft',{'actual_usage':[{'ingredient_id':'chicken','quantity':'300'}]})],
        [('preview_preparation',{})],
    ])
    result=agent.handle('300 g raw.')
    assert result.ok and result.data['preparation_status']=='awaiting_approval'
    draft=agent.workflow.load()['preparation_draft']['data']
    assert draft['prepared_on']=='2026-11-18'
    assert draft['actual_usage'][0]['unit']=='g' and draft['actual_usage'][0]['state']=='raw'
    assert draft['outputs'][0]['boxes']==5


def test_complete_draft_previews_without_reasking_known_details(stocked):
    agent=cooking_agent(stocked,[
        [('update_preparation_draft',complete_details())],
        [('ask_user',{'topic':'quantity'})],
        [('preview_preparation',{})],
    ])
    result=agent.handle('Preview preparing five boxes using the actual quantities I supplied.')
    assert result.ok and result.data['preparation_status']=='awaiting_approval'
    assert result.data['waiting_question'] is None
    assert stocked.store.info()['counts']['cooking_runs']==0


def test_missing_date_and_split_allocations_generate_distinct_questions(stocked):
    from test_batch_completion import ScriptedModel
    details=complete_details()
    del details['prepared_on']
    details['outputs']=[{'name':'lunch','boxes':3},{'name':'curry only','boxes':1}]
    agent=cooking_agent(stocked,[[('update_preparation_draft',details)],[('ask_user',{'topic':'date'})]])
    result=agent.handle('Preview cooking actual usage into three lunch boxes and one curry-only box.')
    assert result.ok and 'what date' in result.data['message']
    agent.client.responses=ScriptedModel([
        [('update_preparation_draft',{'prepared_on':'2026-11-18'})],[('ask_user',{'topic':'details'})],
    ])
    result=agent.handle('2026-11-18')
    assert result.ok and 'went into lunch' in result.data['message']
    draft=agent.workflow.load()['preparation_draft']['data']
    assert draft['outputs']==details['outputs']
    assert draft['prepared_on']=='2026-11-18'


def test_early_stop_is_bounded_and_not_reported_as_preparation_success(stocked):
    from nutrition_demo.display import render
    agent=cooking_agent(stocked,[])
    result=agent.handle(PREVIEW_REQUEST)
    assert not result.ok and result.data['preparation_status']=='incomplete'
    assert result.data['counts']['model_calls']==3
    assert 'All four nutrient targets pass' not in render(result)
    assert stocked.store.info()['counts']['cooking_runs']==0


def test_model_cannot_supply_unchecked_preview_payload_in_draft_scope(stocked):
    agent=cooking_agent(stocked,[
        [('preview_preparation',{'recipe_id':'curry',**supplied_details()})],
        [('preview_preparation',{})],[('preview_preparation',{})],
    ])
    before=stocked.store.info()['counts']['previews']
    result=agent.handle(PREVIEW_REQUEST)
    assert not result.ok and result.data['preparation_status']=='incomplete'
    assert stocked.store.info()['counts']['previews']==before


def test_new_plan_clears_preparation_draft_and_unrelated_requests_do_not_resume_it(stocked):
    from test_batch_completion import ScriptedModel
    agent=cooking_agent(stocked,[[('update_preparation_draft',supplied_details())],[('ask_user',{'topic':'details'})]])
    assert agent.handle(PREVIEW_REQUEST).ok
    agent.client.responses=ScriptedModel([[('list_inventory',{})],[]])
    result=agent.handle('Show inventory.')
    assert result.ok and 'preparation_status' not in result.data
    assert not agent.workflow.load()['preparation_draft']['data'].get('question')
    assert agent.handle('/new-plan').ok
    assert 'preparation_draft' not in agent.workflow.load()


def test_question_displays_captured_facts_without_marking_them_saved(stocked):
    from nutrition_demo.display import render
    agent=cooking_agent(stocked,[[('update_preparation_draft',supplied_details())],[('ask_user',{'topic':'details'})]])
    text=render(agent.handle(PREVIEW_REQUEST))
    assert 'Preparation details captured (not saved)' in text
    assert 'chicken: 300 g(raw)' in text and 'rice: 150 g(dry)' in text
    assert 'Prepared on: 2026-11-18' in text and 'curry: 5 boxes' in text
    assert stocked.store.info()['counts']['cooking_runs']==0


def test_explicit_relative_date_reply_is_normalized_in_application_timezone(stocked):
    from test_batch_completion import ScriptedModel
    details=complete_details()
    del details['prepared_on']
    agent=cooking_agent(stocked,[[('update_preparation_draft',details)],[('ask_user',{'topic':'date'})]])
    assert agent.handle('Preview cooking the actual ingredients into five boxes.').ok
    expected=stocked._day('today')
    agent.client.responses=ScriptedModel([[('update_preparation_draft',{'prepared_on':'today'})],[('preview_preparation',{})]])
    result=agent.handle('Today.')
    assert result.ok and result.data['preparation_status']=='awaiting_approval'
    assert agent.workflow.load()['preparation_draft']['data']['prepared_on']==expected
