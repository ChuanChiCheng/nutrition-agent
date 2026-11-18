from decimal import Decimal as D
from concurrent.futures import ThreadPoolExecutor
import pytest
from nutrition_demo.models import BatchOutput as B, IngredientAllocation as A


def quantities(s):
    return {i['ingredient_id']: D(i['quantity']) for i in s.list_inventory().data['items']}


def split(s):
    return s.preview_preparation('curry',[
        {'ingredient_id':'chicken','quantity':700,'unit':'g','state':'raw'},
        {'ingredient_id':'rice','quantity':600,'unit':'g','state':'dry'},
        {'ingredient_id':'broccoli','quantity':900,'unit':'g','state':'raw'}],
        [B('full',6,[A('chicken',600,'g'),A('rice',600,'g'),A('broccoli',900,'g')]),
         B('curry only',1,[A('chicken',100,'g')])],'2026-11-17')


def test_curry_two_batches_once_and_exact_cost(stocked):
    p=split(stocked)
    assert p.ok,p
    assert quantities(stocked)['chicken']==1000
    r=stocked.confirm_preview(p.data['id'],'split')
    assert r.ok,r
    assert quantities(stocked)=={'chicken':D(300),'rice':D(400),'broccoli':D(100),'yogurt':D(10)}
    batches=stocked.batch_summary().data['batches']
    assert len(batches)==2
    by_name={b['name']:b for b in batches}
    assert by_name['full']['box_nutrients']['kcal']==D(330)
    assert by_name['curry only']['box_nutrients']['kcal']==D(100)
    assert by_name['full']['box_cost']['total']==D('3.5')
    assert stocked.store.info()['counts']['cooking_runs']==1


@pytest.mark.parametrize('allocations',[[A('chicken',101,'g')],[A('chicken',99,'g')],
    [A('chicken',50,'g'),A('chicken',50,'g')],[A('chicken',100,'ml')]])
def test_invalid_allocation_rejected(stocked,allocations):
    p=stocked.preview_preparation('curry',[{'ingredient_id':'chicken','quantity':100,'unit':'g','state':'raw'}],
        [B('bad',1,allocations)],'2026-11-17')
    assert not p.ok
    assert stocked.store.info()['counts']['cooking_runs']==0


def test_dispositions_are_part_of_conservation(stocked):
    p=stocked.preview_preparation('curry',[{'ingredient_id':'chicken','quantity':100,'unit':'g','state':'raw'}],
        [B('smaller',1,[A('chicken',90,'g')])],'2026-11-17',
        [{'cooking_ingredient_id':'chicken','quantity':10,'unit':'g','kind':'loss'}])
    assert p.ok,p
    assert stocked.confirm_preview(p.data['id'],'loss').ok
    assert quantities(stocked)['chicken']==900
    assert stocked.batch_summary().data['batches'][0]['box_nutrients']['kcal']==90


def test_reject_and_insufficient_inventory(stocked):
    p=split(stocked)
    assert stocked.reject_preview(p.data['id']).ok
    assert not stocked.confirm_preview(p.data['id'],'rejected').ok
    assert quantities(stocked)['chicken']==1000
    p=stocked.preview_preparation('curry',[{'ingredient_id':'chicken','quantity':1001,'unit':'g','state':'raw'}],
        [B('too much',1,[A('chicken',1001,'g')])],'2026-11-17')
    assert not p.ok


def test_retry_and_mismatched_request(stocked):
    p=split(stocked)
    first=stocked.confirm_preview(p.data['id'],'repeat')
    assert first.ok
    assert stocked.confirm_preview(p.data['id'],'repeat')==first
    assert not stocked.confirm_preview(p.data['id'],'other').ok
    q=stocked.preview_inventory_change([{'ingredient_id':'chicken','quantity':1,'unit':'g','state':'raw'}],'purchase')
    assert not stocked.confirm_preview(q.data['id'],'repeat').ok
    assert quantities(stocked)['chicken']==300


def test_two_concurrent_confirmations_share_version(stocked):
    p=split(stocked);q=split(stocked)
    with ThreadPoolExecutor(2) as pool:
        results=list(pool.map(lambda pair: stocked.confirm_preview(*pair),[(p.data['id'],'one'),(q.data['id'],'two')]))
    assert sum(r.ok for r in results)==1
    assert quantities(stocked)['chicken']==300


def test_mid_transaction_failure_rolls_back(stocked):
    with stocked.store.transaction() as c:
        c.execute("CREATE FUNCTION fail_batch() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'injected'; END $$")
        c.execute('CREATE TRIGGER fail_insert BEFORE INSERT ON batches FOR EACH ROW EXECUTE FUNCTION fail_batch()')
    p=split(stocked)
    assert not stocked.confirm_preview(p.data['id'],'fail').ok
    assert quantities(stocked)['chicken']==1000
    assert stocked.store.info()['counts']['cooking_runs']==0


def test_addon_confirmation_does_not_consume(prepared):
    s,b=prepared
    p=s.preview_batch_addons(b,[{'ingredient_id':'yogurt','quantity':1,'unit':'serving','state':'packaged'}])
    assert p.ok,p
    assert s.confirm_preview(p.data['id'],'addons').ok
    assert quantities(s)['yogurt']==10
    assert s.store.info()['counts']['events']==0


def test_profile_requires_separate_daily_target(service):
    p=service.set_profile({'timezone':'America/Los_Angeles','meal_targets':{'kcal':600,'protein_g':40,'carbs_g':65,'fat_g':20}})
    assert not p.ok
    p=service.set_profile({'timezone':'America/Los_Angeles','meal_targets':{'kcal':600,'protein_g':40,'carbs_g':65,'fat_g':20},
                          'daily_targets':{'kcal':1800,'protein_g':120,'carbs_g':195,'fat_g':60},'equipment':['6 Qt Instant Pot'],'container_ml':1000})
    assert p.ok
    assert service.get_profile().data['daily_targets']['kcal']=='1800'
