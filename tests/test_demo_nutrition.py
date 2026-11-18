from decimal import Decimal as D
import pytest
from nutrition_demo.models import Nutrients


def test_batch_division_and_cost():
    from nutrition_demo.nutrition import per_box, used_cost
    assert per_box(Nutrients(3600,240,390,120),8) == Nutrients(450,30,'48.75',15)
    assert used_cost(D(12),D(250),D(1000)) == D(3)


@pytest.mark.parametrize('values,passed', [
    ((570,40,'58.5',18),True), ((630,44,'71.5',22),True),
    (('569.999999',40,65,20),False), ((600,'39.999',65,20),False),
    ((600,'44.000001',65,20),False), ((600,40,'71.500001',20),False),
    ((600,40,65,'22.000001'),False)])
def test_unrounded_tolerance(values,passed):
    from nutrition_demo.nutrition import validate_targets
    r = validate_targets(Nutrients(*values),Nutrients(600,40,65,20))
    assert r['passed'] is passed
    assert len(r['metrics']) == 4


@pytest.mark.parametrize('value', ['NaN','Infinity','-1',True])
def test_invalid_nutrients(value):
    with pytest.raises(ValueError):
        Nutrients(value,1,1,1)


def test_invalid_box_and_missing_nutrition():
    from nutrition_demo.nutrition import per_box
    for n in (0,-1,1.5,True):
        with pytest.raises(ValueError):
            per_box(Nutrients(1,1,1,1),n)
    with pytest.raises(ValueError):
        Nutrients.from_dict({'kcal':100})


def test_no_unverified_unit_or_state_conversion():
    from nutrition_demo.nutrition import checked_quantity
    for unit,state in [('ml','raw'),('g','cooked')]:
        with pytest.raises(ValueError):
            checked_quantity('100',unit,state,{'unit':'g','state':'raw'})


def test_unknown_cost_not_zero():
    from nutrition_demo.nutrition import aggregate_cost
    assert aggregate_cost([D(3),None]) == {'known_subtotal': D(3), 'complete': False, 'total': None}


def test_catalog_separates_history_and_proposal():
    from nutrition_demo.catalog import Catalog
    c=Catalog.load()
    assert len(c.recipes)==4
    n=c.recipe('nikujaga')
    assert n['versions'][0]['status']=='historical_record'
    assert n['versions'][0]['boxes']==6
    assert n['versions'][1]['status']=='unconfirmed_plan'
    assert c.recipe('curry')['versions'][0]['outputs'][1]['boxes']==1
    assert all(r['steps'] and r['equipment'] and r['difficulty'] for r in c.recommend([],{}))
    assert all(s['sha256'] and s['pages'] for s in c.manifest['recipes'])


def test_proposal_validates_and_flags_unknown_sources():
    from nutrition_demo.catalog import Catalog
    c=Catalog.load()
    r=c.calculate('curry',[{'ingredient_id':'chicken','quantity':'100','unit':'g','state':'raw'}],1,Nutrients(600,40,65,20))
    assert r['targets']['passed'] is False
    assert r['nutrients']['protein_g'] == D('22.5')
    with pytest.raises(ValueError,match='identity'):
        c.validate_proposal('curry',[{'ingredient_id':'rice','quantity':100,'unit':'g','state':'dry'}])
    with pytest.raises(ValueError,match='nutrition'):
        c.calculate('curry',[{'ingredient_id':'broth','quantity':100,'unit':'ml','state':'packaged'}],1)


def test_suggestion_does_not_claim_pass_on_single_metric():
    from nutrition_demo.catalog import Catalog
    r=Catalog.load().suggest_additions(Nutrients(600,39,65,20),Nutrients(600,40,65,20))
    assert r
    assert all('targets' in x and 'meal_nutrients' in x for x in r)


def test_exact_division_without_rounded_reciprocal():
    from nutrition_demo.nutrition import per_box,scale_nutrients
    assert per_box(Nutrients(1980,0,0,0),6).kcal==D(330)
    assert scale_nutrients(Nutrients(700,0,0,0),D(600),D(700)).kcal==D(600)


def test_only_one_minor_new_ingredient_substitution():
    from nutrition_demo.catalog import Catalog
    c=Catalog.load()
    c.recipes['curry']['allowed_substitutions']=['mushroom','beef']
    base=[{'ingredient_id':i,'quantity':100,'unit':c.ingredient(i)['unit'],'state':c.ingredient(i)['state']} for i in ['chicken','potato','curry_block']]
    assert c.validate_proposal('curry',base+[{'ingredient_id':'mushroom','quantity':100,'unit':'g','state':'raw'}])
    with pytest.raises(ValueError,match='substitution'):
        c.validate_proposal('curry',base+[{'ingredient_id':'mushroom','quantity':100,'unit':'g','state':'raw'},
                                         {'ingredient_id':'beef','quantity':100,'unit':'g','state':'raw'}])


def test_verified_product_links_include_package_counts():
    from nutrition_demo.catalog import Catalog
    recipes=Catalog.load().recommend([],{})
    curry=next(r for r in recipes if r['id']=='curry')
    shopping={i['ingredient_id']:i for i in curry['shopping']}
    assert shopping['curry_block']['packages_needed']==3
    assert shopping['broccoli']['packages_needed']==1
    assert shopping['curry_block']['link_status']=='verified_product_page'


def test_customized_steps_use_confirmed_quantities():
    from nutrition_demo.catalog import Catalog
    c=Catalog.load()
    items=[{'ingredient_id':i,'quantity':q,'unit':c.ingredient(i)['unit'],'state':c.ingredient(i)['state']}
           for i,q in [('chicken','1200'),('potato','600'),('curry_block','184'),('rice','480')]]
    r=c.calculate('curry',items,6)
    text='\n'.join(r['instructions'])
    assert '600' in text and '92' in text
    assert '1097' not in text and '1097' not in text.replace(',','')
    assert '花椰菜' not in text


def test_source_unquantified_ingredients_become_valid_after_quantity_and_label_supplied():
    from nutrition_demo.catalog import Catalog
    c=Catalog.load()
    # Supply controlled test labels for every currently missing brand; no assumptions about actual foods.
    for ref in c.ingredients.values():
        if ref.get('nutrients') is None:
            ref['nutrients']={'kcal':'1','protein_g':'1','carbs_g':'1','fat_g':'1'}
            ref['source']={'status':'synthetic'}
    rice=[*c.recipe('rice_pot')['ingredients'],
          {'ingredient_id':'canned_chicken','quantity':800,'unit':'g','state':'drained'},
          {'ingredient_id':'garlic','quantity':18,'unit':'g','state':'raw'},
          {'ingredient_id':'oil','quantity':10,'unit':'g','state':'packaged'}]
    assert c.validate_proposal('rice_pot',rice)
    curry=[*c.recipe('curry')['ingredients'],{'ingredient_id':'garlic','quantity':12,'unit':'g','state':'raw'},
           {'ingredient_id':'oil','quantity':10,'unit':'g','state':'packaged'}]
    assert c.validate_proposal('curry',curry)
