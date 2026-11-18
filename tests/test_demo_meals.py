from decimal import Decimal as D
from nutrition_demo.models import BatchOutput as B,IngredientAllocation as A
from test_demo_preparation import quantities


def add_yogurt(s,b,qty=1):
    p=s.preview_batch_addons(b,[{'ingredient_id':'yogurt','quantity':qty,'unit':'serving','state':'packaged'}])
    assert p.ok,p
    assert s.confirm_preview(p.data['id'],'addon-'+str(qty)).ok


def test_one_box_plus_confirmed_addon(prepared):
    s,b=prepared;add_yogurt(s,b)
    r=s.log_meal(b,'today','dinner','meal1')
    assert r.ok,r
    assert r==s.log_meal(b,'today','dinner','meal1')
    assert quantities(s)['yogurt']==9
    assert s.batch_summary().data['batches'][0]['remaining_boxes']==7
    day=s.daily_summary('2026-11-17').data
    assert day['total']=={'kcal':D(300),'protein_g':D('27.5'),'carbs_g':D(33),'fat_g':D('3.5')}
    assert day['box']['kcal']==200
    assert day['addons']['kcal']==100
    assert day['scope']=='recorded_prepared_meals_only'


def test_skip_addon_and_history_snapshot(prepared):
    s,b=prepared;add_yogurt(s,b)
    assert s.log_meal(b,'2026-11-17',None,'skip',[]).ok
    assert quantities(s)['yogurt']==10
    assert s.log_meal(b,'2026-11-17',None,'with').ok
    add_yogurt(s,b,2)
    assert s.daily_summary('2026-11-17').data['total']['kcal']==500
    assert quantities(s)['yogurt']==9
    assert s.batch_summary().data['batches'][0]['meal_nutrients']['kcal']==400


def test_zero_boxes_rejected(prepared):
    s,b=prepared
    for i in range(8):assert s.log_meal(b,'today',None,str(i)).ok
    assert not s.log_meal(b,'today',None,'too-many').ok
    assert s.store.info()['counts']['events']==8


def test_insufficient_addon_and_reconciled_atomic_meal(prepared):
    s,b=prepared;add_yogurt(s,b,11)
    r=s.log_meal(b,'today','lunch','short')
    assert not r.ok and 'clarification' in r.error
    assert s.store.info()['counts']['events']==0
    assert quantities(s)['yogurt']==10
    p=s.preview_reconciled_meal([{'ingredient_id':'yogurt','quantity':1,'unit':'serving','state':'packaged'}],
        {'batch_id':b,'eaten_on':'today','meal':'lunch'},mode='purchase')
    assert p.ok,p
    assert s.confirm_preview(p.data['id'],'reconciled').ok
    assert quantities(s)['yogurt']==0
    assert s.store.info()['counts']['events']==1


def test_reconciled_failure_rolls_back(prepared):
    s,b=prepared;add_yogurt(s,b,11)
    with s.store.transaction() as c:
        c.execute("CREATE FUNCTION fail_event() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'injected'; END $$")
        c.execute('CREATE TRIGGER fail_insert BEFORE INSERT ON events FOR EACH ROW EXECUTE FUNCTION fail_event()')
    p=s.preview_reconciled_meal([{'ingredient_id':'yogurt','quantity':1,'unit':'serving','state':'packaged'}],
        {'batch_id':b,'eaten_on':'today','meal':None},mode='purchase')
    assert p.ok,p
    assert not s.confirm_preview(p.data['id'],'fail').ok
    assert quantities(s)['yogurt']==10
    assert s.batch_summary().data['batches'][0]['remaining_boxes']==8


def test_ambiguous_batch_candidates_not_automatic(stocked):
    s=stocked
    p=s.preview_preparation('curry',[{'ingredient_id':'chicken','quantity':200,'unit':'g','state':'raw'}],
        [B('same',1,[A('chicken',100,'g')]),B('same',1,[A('chicken',100,'g')])],'today')
    assert s.confirm_preview(p.data['id'],'prep').ok
    r=s.find_batches('same')
    assert r.data['needs_clarification']
    assert len(r.data['candidates'])==2
    assert not s.log_meal('same','today',None,'ambiguous').ok
    assert s.store.info()['counts']['events']==0


def test_yesterday_uses_local_midnight(prepared):
    s,b=prepared
    assert s.log_meal(b,'yesterday',None,'yesterday').ok
    assert s.daily_summary('2026-11-16').data['total']['kcal']==200
    assert s.daily_summary('2026-11-17').data['total']['kcal']==0
