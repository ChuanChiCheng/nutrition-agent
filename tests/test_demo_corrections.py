from datetime import timedelta
from decimal import Decimal as D
import pytest
from nutrition_demo.models import BatchOutput as B,IngredientAllocation as A
from test_demo_preparation import quantities
from test_demo_meals import add_yogurt


def event(s,b,key='meal'):
    r=s.log_meal(b,'2026-11-17','lunch',key)
    assert r.ok,r
    return r.data['event_id']


def test_date_moves_snapshot_without_consumption(prepared):
    s,b=prepared;add_yogurt(s,b);e=event(s,b)
    before=quantities(s)
    p=s.preview_correction(e,{'date':'2026-11-16'})
    assert p.ok,p
    assert s.daily_summary('2026-11-17').data['total']['kcal']==300
    assert s.confirm_preview(p.data['id'],'correct').ok
    assert quantities(s)==before
    assert s.daily_summary('2026-11-17').data['total']['kcal']==0
    assert s.daily_summary('2026-11-16').data['total']['kcal']==300
    assert s.batch_summary().data['batches'][0]['remaining_boxes']==7
    assert s.find_events({'date':'2026-11-16'}).data['candidates'][0]['id']==e


def test_date_uses_historical_addon_after_plan_change(prepared):
    s,b=prepared;add_yogurt(s,b);e=event(s,b);add_yogurt(s,b,2)
    p=s.preview_correction(e,{'date':'2026-11-16'})
    assert s.confirm_preview(p.data['id'],'date-history').ok
    assert s.daily_summary('2026-11-16').data['total']['kcal']==300
    assert quantities(s)['yogurt']==9


def test_remove_historical_addon_restores_original_amount(prepared):
    s,b=prepared;add_yogurt(s,b);e=event(s,b);add_yogurt(s,b,2)
    p=s.preview_correction(e,{'addon_override':[]})
    assert p.ok,p
    assert any(x.get('ingredient_id')=='yogurt' and D(x['inventory_delta'])==1 for x in p.data['changes'])
    assert s.confirm_preview(p.data['id'],'no-addon').ok
    assert quantities(s)['yogurt']==10
    assert s.daily_summary('today').data['total']['kcal']==200


def test_change_batch_restores_source_and_uses_target_addon(prepared):
    s,b=prepared;add_yogurt(s,b);e=event(s,b)
    p=s.preview_preparation('curry',[{'ingredient_id':'chicken','quantity':100,'unit':'g','state':'raw'}],
        [B('new',1,[A('chicken',100,'g')])],'today')
    b2=s.confirm_preview(p.data['id'],'prepare2').data['batch_ids'][0]
    p=s.preview_correction(e,{'batch_id':b2})
    assert p.ok,p
    assert s.confirm_preview(p.data['id'],'swap').ok
    by={x['id']:x for x in s.batch_summary().data['batches']}
    assert by[b]['remaining_boxes']==8 and by[b2]['remaining_boxes']==0
    assert quantities(s)['yogurt']==10
    assert s.daily_summary('today').data['total']['kcal']==100


def test_refused_stale_unauthorized_and_empty_correction(prepared):
    s,b=prepared;e=event(s,b)
    assert not s.preview_correction(e,{}).ok
    assert not s.preview_correction(e,{'date':'2026-11-17'}).ok
    p=s.preview_correction(e,{'date':'2026-11-16'})
    assert not s.confirm_preview(p.data['id'],'bot',actor='model').ok
    assert s.reject_preview(p.data['id']).ok
    assert not s.confirm_preview(p.data['id'],'rejected').ok
    p=s.preview_correction(e,{'date':'2026-11-16'})
    assert s.log_meal(b,'today',None,'other').ok
    assert not s.confirm_preview(p.data['id'],'stale').ok
    assert s.daily_summary('today').data['events']==2


def test_expired_preview(prepared):
    s,b=prepared;e=event(s,b)
    p=s.preview_correction(e,{'date':'2026-11-16'})
    now=s.clock();s.clock=lambda:now+timedelta(minutes=31)
    assert not s.confirm_preview(p.data['id'],'expired').ok


def test_lost_response_then_other_write_then_retry(prepared):
    s,b=prepared;e=event(s,b)
    p=s.preview_correction(e,{'date':'2026-11-16'})
    committed=s.confirm_preview(p.data['id'],'lost-response')
    assert committed.ok
    assert s.log_meal(b,'today',None,'after').ok
    assert s.confirm_preview(p.data['id'],'lost-response')==committed
    assert s.daily_summary('2026-11-16').data['events']==1
    assert s.store.info()['counts']['events']==2


def test_failed_transaction_retry_same_id(prepared):
    s,b=prepared;e=event(s,b)
    with s.store.transaction() as c:
        c.execute("CREATE FUNCTION fail_update() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'injected'; END $$")
        c.execute('CREATE TRIGGER fail_change BEFORE UPDATE ON events FOR EACH ROW EXECUTE FUNCTION fail_update()')
    p=s.preview_correction(e,{'date':'2026-11-16'})
    assert not s.confirm_preview(p.data['id'],'retry').ok
    assert s.daily_summary('today').data['events']==1
    with s.store.transaction() as c:c.execute('DROP TRIGGER fail_change ON events')
    assert s.confirm_preview(p.data['id'],'retry').ok
    assert s.daily_summary('2026-11-16').data['events']==1


def test_correction_rejects_unknown_addon_and_insufficient_stock(prepared):
    s,b=prepared;e=event(s,b)
    assert not s.preview_correction(e,{'addon_override':[{'ingredient_id':'missing','quantity':1,'unit':'g','state':'raw'}]}).ok
    assert not s.preview_correction(e,{'addon_override':[{'ingredient_id':'yogurt','quantity':11,'unit':'serving','state':'packaged'}]}).ok
    assert quantities(s)['yogurt']==10
