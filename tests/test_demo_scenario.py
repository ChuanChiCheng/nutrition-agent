from decimal import Decimal as D
from nutrition_demo.store import Store


def test_six_planned_eight_actual_seven_after_correction_reopen(store):
    from nutrition_demo.scenario import run_scripted,load_scenario
    seed=load_scenario()
    store.seed(seed)
    r=run_scripted(store)
    assert r['synthetic'] is True
    assert r['planned_boxes']==6 and r['actual_boxes']==8
    assert r['remaining_boxes']==7
    assert r['inventory']=={'fixture_mix':'200','fixture_yogurt':'9'}
    assert r['corrected_summary']['total']['kcal']=='550'
    reopened=Store(store.dsn,store.schema)
    assert reopened.info()['counts']['events']==1
    assert reopened.info()['counts']['batches']==1
    assert r['trace_steps']==['inventory_confirmed','recipe_selected','proposal_calculated','recipe_accepted',
                              'preparation_confirmed','addons_confirmed','meal_recorded','date_corrected']


def test_same_case_semantics_on_two_schemas(store):
    import psycopg
    from psycopg import sql
    from nutrition_demo.scenario import run_scripted,load_scenario
    other_schema=store.schema+'_copy'
    with psycopg.connect(store.dsn,autocommit=True) as c:c.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(other_schema)))
    other=Store(store.dsn,other_schema)
    try:
        other.migrate()
        store.seed(load_scenario());other.seed(load_scenario())
        first=run_scripted(store);second=run_scripted(other)
        assert first==second
    finally:
        with psycopg.connect(store.dsn,autocommit=True) as c:c.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(other_schema)))


def test_bbq_five_with_vegetable_two_without(stocked):
    from nutrition_demo.models import BatchOutput as B,IngredientAllocation as A
    s=stocked
    p=s.preview_preparation('curry',[{'ingredient_id':'chicken','quantity':700,'unit':'g','state':'raw'},
                                   {'ingredient_id':'broccoli','quantity':500,'unit':'g','state':'raw'}],
        [B('with',5,[A('chicken',500,'g'),A('broccoli',500,'g')]),
         B('without',2,[A('chicken',200,'g')])],'today')
    assert s.confirm_preview(p.data['id'],'bbq-shape').ok
    by={b['name']:b for b in s.batch_summary().data['batches']}
    assert by['with']['remaining_boxes']==5 and by['without']['remaining_boxes']==2
    assert by['with']['box_nutrients']['kcal']==120
    assert by['without']['box_nutrients']['kcal']==100
    assert s.store.info()['counts']['cooking_ingredients']==2
