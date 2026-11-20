import pytest

from nutrition_demo.models import Result,Nutrients
from nutrition_demo.display import render,preview


@pytest.mark.parametrize('successful', [True, False])
def test_meal_tool_receipt_identifies_saved_batch_date_and_meal_only_on_success(successful):
    data={
        'event_id':'meal-event', 'batch_id':'batch-1',
        'batch_name':'Synthetic curry lunch batch', 'eaten_on':'2026-11-18', 'meal':'dinner',
        'total_nutrients':{'kcal':600,'protein_g':40,'carbs_g':65,'fat_g':20},
    }
    text=render(Result(True,{'tool_results':[{
        'name':'log_meal',
        'result':{'ok':successful,'data':data,'error':None if successful else 'Write failed'},
    }]}))

    if successful:
        assert 'Meal record updated: meal-event' in text
        assert 'Batch: Synthetic curry lunch batch' in text
        assert 'Date: 2026-11-18' in text
        assert 'Meal: dinner' in text
        assert 'This meal: 600 kcal | Protein 40 g | Carbohydrates 65 g | Fat 20 g' in text
    else:
        assert 'Write failed' in text
        assert 'Meal record updated' not in text
        assert 'Batch: Synthetic curry lunch batch' not in text


def test_proposal_shows_nutrition_cost_steps_and_gap_before_confirmation():
    from nutrition_demo.catalog import Catalog
    c=Catalog.load()
    ingredients=[{'ingredient_id':i,'quantity':q,'unit':c.ingredient(i)['unit'],'state':c.ingredient(i)['state']}
                 for i,q in [('chicken',1200),('potato',600),('curry_block',184)]]
    calculation=c.calculate('curry',ingredients,6,Nutrients(600,40,65,20))
    text=render(Result(True,{'items':ingredients,'boxes':6,'calculation':calculation}))
    assert 'Per box' in text and 'kcal' in text
    assert 'cost' in text and 'Difference' in text and 'Current cooking steps' in text
    assert 'Ingredient inventory' not in text


def test_addon_suggestions_show_whole_meal_validation_without_marking_as_eaten():
    from nutrition_demo.catalog import Catalog
    suggestions=Catalog.load().suggest_additions(Nutrients(500,30,60,15),Nutrients(600,40,65,20))
    text=render(Result(True,{'suggestions':suggestions}))
    assert 'Whole meal' in text and 'kcal' in text and 'no intake recorded' in text
    assert 'Difference' in text


def test_daily_summary_shows_per_nutrient_progress_and_difference():
    data={'day':'2026-11-17','scope':'recorded_prepared_meals_only','events':1,
          'box':{'kcal':500,'protein_g':30,'carbs_g':60,'fat_g':15},
          'addons':{'kcal':0,'protein_g':0,'carbs_g':0,'fat_g':0},
          'total':{'kcal':500,'protein_g':30,'carbs_g':60,'fat_g':15},
          'daily_targets':{'kcal':1800,'protein_g':120,'carbs_g':195,'fat_g':60},
          'progress':{'kcal':{'actual':500,'target':1800,'difference':-1300,'ratio':'0.2777777778'}}}
    text=render(Result(True,data))
    assert 'Calories: 500 / 1800(27.78%)' in text and 'Difference -1300' in text


def test_profile_and_label_previews_show_capacity_and_price():
    data={'id':'preview','summary':'Confirm資料','changes':[
        {'profile':{'meal_targets':{'kcal':600,'protein_g':40,'carbs_g':65,'fat_g':20},
                    'daily_targets':{'kcal':1800,'protein_g':120,'carbs_g':195,'fat_g':60},
                    'timezone':'America/Los_Angeles','equipment':['pot'],'container_ml':1000}},
        {'ingredient_id':'rice','label':{'reference_quantity':100,'nutrients':{'kcal':360,'protein_g':7,'carbs_g':80,'fat_g':1},
                                         'source':{'note':'package photo'},'price':{'usd':4.5,'quantity':2000}}}]}
    text=preview(data)
    assert 'Reference container capacity: 1000 ml' in text
    assert 'Package price: US$4.5 / 2000 reference units' in text
