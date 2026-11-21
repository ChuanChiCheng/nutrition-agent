"""Missing saved meals are distinct from zero totals, ambiguity and failures."""
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
import pytest
import psycopg

from nutrition_demo.display import render


def record(service,batch,meal='lunch',key='event',day='2026-11-10'):
    result=service.log_meal(batch,day,meal,key)
    assert result.ok,result
    return result.data['event_id']


def test_empty_event_search_is_absence_not_ambiguity(prepared):
    from nutrition_eval.state import read_business_state
    service,_=prepared
    before=read_business_state(service.store)
    result=service.find_events({'date':'2026-11-10','meal':'lunch'})
    assert result.ok
    assert result.data['match_status']=='no_match'
    assert result.data['candidates']==[]
    assert result.data['needs_clarification'] is False
    assert result.data['query']=={'date':'2026-11-10','meal':'lunch'}
    assert result.data['record_scope']=='recorded_prepared_meals_only'
    assert read_business_state(service.store)==before
    text=render(result)
    assert '2026-11-10' in text and 'lunch' in text
    assert 'No recorded prepared meals match' in text
    assert 'dish and exact nutrition are unknown' in text
    assert 'Select one' not in text and '0 kcal' not in text


def test_event_query_echo_uses_normalized_application_date(prepared):
    service,_=prepared
    service.clock=lambda:datetime.fromisoformat('2026-11-18T12:00:00-08:00')
    result=service.find_events({'date':'yesterday','meal':'dinner'})
    assert result.ok
    assert result.data['query']=={'date':'2026-11-17','meal':'dinner'}


def test_unique_lookup_uses_saved_snapshot_not_current_default_addons(prepared):
    from test_demo_meals import add_yogurt
    service,batch=prepared
    event=record(service,batch)
    add_yogurt(service,batch)
    result=service.find_events({'event_id':event})
    assert result.data['match_status']=='unique'
    assert not result.data['needs_clarification']
    text=render(result)
    assert event in text and '2026-11-10' in text and 'lunch' in text
    assert 'Saved nutrition: 200 kcal' in text
    assert '300 kcal' not in text


def test_multiple_read_results_do_not_require_selection(prepared):
    service,batch=prepared
    first=record(service,batch,key='first')
    second=record(service,batch,meal='dinner',key='second')
    result=service.find_events({'date':'2026-11-10'})
    assert result.data['match_status']=='multiple'
    assert result.data['needs_clarification'] is True  # Compatibility for single-record operations.
    text=render(result)
    assert first in text and second in text
    assert 'lunch' in text and 'dinner' in text
    assert 'Select one' not in text
    assert 'recorded prepared meals' in text


def test_missing_lunch_is_unknown_even_when_dinner_exists(prepared):
    service,batch=prepared
    record(service,batch,meal='dinner')
    result=service.find_events({'date':'2026-11-10','meal':'lunch'})
    assert result.data['match_status']=='no_match'
    text=render(result)
    assert 'unknown' in text and '200 kcal' not in text and '0 kcal' not in text
    assert service.daily_summary('2026-11-10').data['total']['kcal']==Decimal('200')


def test_empty_daily_summary_preserves_zero_recorded_total_and_unknown_intake(prepared):
    service,_=prepared
    result=service.daily_summary('2026-11-10')
    assert result.ok and result.data['events']==0
    assert result.data['total']['kcal']==0
    text=render(result)
    assert 'No prepared meals are recorded for this date.' in text
    assert 'Recorded total: 0 kcal' in text
    assert 'Actual intake is unknown' in text


def test_database_failure_is_not_reported_as_no_match(prepared,monkeypatch):
    service,_=prepared
    @contextmanager
    def unavailable(**kwargs):
        raise psycopg.OperationalError('offline failure injection')
        yield
    monkeypatch.setattr(service.store,'transaction',unavailable)
    result=service.find_events({'date':'2026-11-10','meal':'lunch'})
    assert not result.ok
    assert 'match_status' not in result.data
    text=render(result)
    assert 'database_transaction_failed' in text
    assert 'No recorded' not in text and '0 kcal' not in text


def test_invalid_date_is_not_reported_as_no_match(prepared):
    service,_=prepared
    result=service.find_events({'date':'not-a-date'})
    assert not result.ok and 'match_status' not in result.data


@pytest.mark.parametrize('message,expected', [
    ('How many calories were in my homemade lunch on November 10, 2026?',{'date':'2026-11-10','meal':'lunch'}),
    ('What dish did I eat on November 10, and how many calories did it contain?',{'date':'2026-11-10'}),
    ('Show my recorded dinner on 2026-11-10.',{'date':'2026-11-10','meal':'dinner'}),
    ('What did I eat for lunch yesterday?',{'date':'2026-11-17','meal':'lunch'}),
])
def test_meal_lookup_binds_explicit_date_and_requested_meal(message,expected):
    from nutrition_demo.meal_lookup import MealHistoryLookup
    lookup=MealHistoryLookup.from_message(message,'2026-11-18')
    assert lookup is not None
    assert lookup.query==expected


@pytest.mark.parametrize('message', [
    'Correct the November 10 lunch record to dinner.',
    'Can you correct my lunch on November 10 to dinner?',
    'How many calories were in lunch on November 10? Record it.',
    'Summarize daily totals for November 10.',
    'How many calories were in my lunch?',
    'What did I eat for lunch on November 10 and November 11?',
    'What did I eat for lunch and dinner on November 10?',
    'Does the meal batch meet its meal targets?',
    'What is the recipe for lunch on November 10?',
    'What did I eat for lunch before November 10?',
    'What did I eat for lunch on November 10 last year?',
    'What did I eat for lunch on November 10 and 11?',
    'What did I eat for lunch on November 10–11?',
    'What did I eat for lunch on November 10? Please fix its nutrition.',
    'What did I eat for lunch on November 10? Please edit its nutrition.',
    'Show my lunch on November 10 and add yogurt to my default addons.',
    'Find my lunch on November 10 and set its meal to dinner.',
    'Show my meals from November 10 through 12.',
    'Show my lunch on the day before November 10.',
    'What should I eat for lunch on November 21?',
    'How many calories should my lunch have on November 21?',
    'What meal can I make for lunch on November 21?',
    'Show me a meal I can make for lunch on November 21.',
    'Show my lunch on November 10 and buy 2 servings of yogurt.',
    'Show my lunch on November 10 and purchase yogurt.',
    'Show my meals on November 10 & 11.',
    'Show my lunch on November 10 of 2025.',
    'Show my lunch at the restaurant on November 10.',
])
def test_other_requests_do_not_enter_terminal_history_handling(message):
    from nutrition_demo.meal_lookup import MealHistoryLookup
    assert MealHistoryLookup.from_message(message,'2026-11-18') is None


def make_agent(service,steps):
    from test_batch_completion import make_agent as offline_agent
    return offline_agent(service,steps)


def test_missing_meal_lookup_finishes_before_aggregate_or_irrelevant_question(prepared):
    service,batch=prepared
    record(service,batch,meal='dinner')
    agent=make_agent(service,[
        [('find_events',{'query':{'date':'2026-11-10','meal':'lunch'}}),
         ('daily_summary',{'day':'2026-11-10'}),('ask_user',{'topic':'event'})],
    ])
    result=agent.handle('How many calories were in my homemade lunch on November 10, 2026?')
    assert result.ok,result
    assert result.data['meal_lookup_status']=='no_match'
    assert result.data['counts']=={'model_calls':1,'tool_calls':1}
    assert [r['name'] for r in result.data['tool_results']]==['find_events']
    text=render(result)
    assert 'dish and exact nutrition are unknown' in text
    assert '0 kcal' not in text and '200 kcal' not in text
    assert 'corrected' not in text and 'Clarification needed' not in text
    assert service.store.info()['counts']['events']==1


@pytest.mark.parametrize('search_meal',['lunch',' Lunch '])
def test_title_case_saved_meal_is_found_without_changing_its_snapshot(prepared,search_meal):
    service,batch=prepared
    saved=record(service,batch,meal=' Lunch ')
    result=service.find_events({'date':'2026-11-10','meal':search_meal})
    assert result.data['match_status']=='unique'
    assert result.data['query']=={'date':'2026-11-10','meal':'lunch'}
    assert result.data['candidates'][0]['meal']==' Lunch '
    assert result.data['candidates'][0]['data']['meal']==' Lunch '
    agent=make_agent(service,[[('find_events',{'query':{'date':'2026-11-10','meal':search_meal}})]])
    answer=agent.handle('Show my Lunch on November 10, 2026.')
    assert answer.ok and answer.data['meal_lookup_status']=='unique'
    assert saved in render(answer)
    assert 'No recorded prepared meals match' not in render(answer)


def test_wrong_or_over_filtered_search_cannot_prove_missing_meal(prepared):
    service,batch=prepared
    saved=record(service,batch)
    agent=make_agent(service,[
        [('find_events',{'query':{'date':'2026-11-11','meal':'lunch'}})],
        [('find_events',{'query':{'date':'2026-11-10','meal':'lunch','batch_id':'wrong'}})],
        [('find_events',{'query':{'date':'2026-11-10','meal':'lunch'}})],
    ])
    result=agent.handle('How many calories were in my lunch on 2026-11-10?')
    assert result.ok and result.data['meal_lookup_status']=='unique'
    text=render(result)
    assert saved in text and 'Saved nutrition: 200 kcal' in text
    assert 'No recorded prepared meals match' not in text


def test_read_only_history_lookup_cannot_create_preview_or_replace_answer_with_totals(prepared):
    service,batch=prepared
    agent=make_agent(service,[
        [('preview_batch_addons',{'batch_id':batch,'items':[]})],
        [('daily_summary',{'day':'2026-11-10'})],
        [('find_events',{'query':{'date':'2026-11-10'}})],
    ])
    before=service.store.info()['counts']
    result=agent.handle('What dish did I eat on November 10, and how many calories did it contain?')
    assert result.ok and result.data['meal_lookup_status']=='no_match'
    after=service.store.info()['counts']
    for table in ('previews','events','inventory_movements','operations'):
        assert after[table]==before[table]
    assert '0 kcal' not in render(result)


def test_history_search_failure_is_an_error_not_a_negative_answer(prepared,monkeypatch):
    from nutrition_demo.models import Result
    service,_=prepared
    monkeypatch.setattr(service,'find_events',lambda query:Result(False,{},'database_transaction_failed'))
    agent=make_agent(service,[[('find_events',{'query':{'date':'2026-11-10','meal':'lunch'}})]])
    result=agent.handle('How many calories were in my lunch on 2026-11-10?')
    assert not result.ok and result.data['meal_lookup_status']=='error'
    text=render(result)
    assert 'database_transaction_failed' in text
    assert 'No recorded prepared meals match' not in text and 'dish and exact nutrition are unknown' not in text


def test_broad_date_lookup_lists_multiple_saved_records_without_selection(prepared):
    service,batch=prepared
    first=record(service,batch,key='first')
    second=record(service,batch,meal='dinner',key='second')
    agent=make_agent(service,[[('find_events',{'query':{'date':'2026-11-10'}})]])
    result=agent.handle('What dish did I eat on 2026-11-10?')
    assert result.ok and result.data['meal_lookup_status']=='multiple'
    text=render(result)
    assert first in text and second in text and 'Select one' not in text


def test_read_lookup_does_not_change_an_existing_pending_approval(prepared):
    service,batch=prepared
    agent=make_agent(service,[[('preview_batch_addons',{'batch_id':batch,'items':[]})]])
    preview=agent.handle('Set the default addons to none.')
    preview_id=preview.data['pending_preview']
    from test_batch_completion import ScriptedModel
    agent.client.responses=ScriptedModel([[('find_events',{'query':{'date':'2026-11-10','meal':'lunch'}})]])
    result=agent.handle('How many calories were in my lunch on November 10?')
    assert result.ok and result.data['meal_lookup_status']=='no_match'
    assert agent.workflow.load()['pending_preview']==preview_id
    assert 'Review the preview' not in render(result)
    assert agent.handle('/reject '+preview_id).ok


@pytest.mark.parametrize('controller_kind',['agent','baseline'])
def test_correction_no_match_preserves_state_and_does_not_enter_lookup_mode(prepared,controller_kind):
    from nutrition_demo.agent import Settings
    from nutrition_demo.workflow import Workflow
    from nutrition_eval.baseline import FixedWorkflowBaseline
    from test_eval_controllers import FakeClient
    service,_=prepared
    query={'date':'2026-11-10','meal':'lunch'}
    if controller_kind=='agent':
        controller=make_agent(service,[[('find_events',{'query':query})],[]])
    else:
        controller=FixedWorkflowBaseline(service,Workflow(service),FakeClient({
            'action':'correct_meal','arguments':{'query':query,'changes':{'date':'2026-11-11'}},'reply':'Review correction.',
        }),Settings())
    before=service.store.info()['counts']
    result=controller.handle('Correct the lunch record on November 10 to November 11.')
    assert result.ok and 'meal_lookup_status' not in result.data
    after=service.store.info()['counts']
    for table in ('events','previews','operations'):
        assert after[table]==before[table]
    assert 'No recorded prepared meals match' in render(result)
    assert not controller.workflow.load().get('pending_preview')


@pytest.mark.parametrize('controller_kind',['agent','baseline'])
@pytest.mark.parametrize('outcome',['confirm','reject'])
def test_ambiguous_correction_still_requires_selection_and_external_approval(prepared,controller_kind,outcome):
    from nutrition_demo.agent import Settings
    from nutrition_demo.workflow import Workflow
    from nutrition_eval.baseline import FixedWorkflowBaseline
    from test_eval_controllers import FakeClient
    from test_batch_completion import ScriptedModel
    service,batch=prepared
    first=record(service,batch,key='first')
    second=record(service,batch,key='second')
    query={'date':'2026-11-10','meal':'lunch'}
    changes={'date':'2026-11-11'}
    if controller_kind=='agent':
        controller=make_agent(service,[[('find_events',{'query':query})],[('ask_user',{'topic':'event'})]])
    else:
        controller=FixedWorkflowBaseline(service,Workflow(service),FakeClient(
            {'action':'correct_meal','arguments':{'query':query,'changes':changes},'reply':'Review correction.'},
            {'action':'correct_meal','arguments':{'query':{'event_id':first},'changes':{}},'reply':'Review correction.'},
        ),Settings())
    result=controller.handle('Correct my lunch record on November 10 to November 11.')
    assert result.ok and 'meal_lookup_status' not in result.data
    assert 'Which meal record' in render(result)
    assert first in render(result) and second in render(result)
    assert not controller.workflow.load().get('pending_preview')
    if controller_kind=='agent':
        controller.client.responses=ScriptedModel([
            [('find_events',{'query':{'event_id':first}})],
            [('preview_correction',{'event_id':first,'changes':changes})],
        ])
    preview=controller.handle(first)
    assert preview.ok
    preview_id=preview.data['pending_preview']
    assert not controller.handle('/confirm wrong-preview').ok
    assert not service.confirm_preview(preview_id,'model-attempt',actor='model').ok
    old=service.find_events({'event_id':first}).data['candidates'][0]
    assert old['eaten_on']=='2026-11-10'
    assert controller.handle('/'+outcome+' '+preview_id).ok
    current=service.find_events({'event_id':first}).data['candidates'][0]
    assert current['eaten_on']==('2026-11-11' if outcome=='confirm' else '2026-11-10')
    assert current['data']['total_nutrients']==old['data']['total_nutrients']
    assert service.find_events({'event_id':second}).data['candidates'][0]['eaten_on']=='2026-11-10'
