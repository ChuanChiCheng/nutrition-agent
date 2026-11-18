import os
import uuid
from datetime import datetime, timezone
import pytest
import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

@pytest.fixture
def store():
    from nutrition_demo.store import Store
    dsn = os.environ.get('TEST_DATABASE_URL')
    if not dsn:
        pytest.fail('TEST_DATABASE_URL required; never fall back to DATABASE_URL')
    info = conninfo_to_dict(dsn)
    if info.get('dbname') != 'nutrition_test' or info.get('host') != 'db_test':
        pytest.fail('Tests require db_test/nutrition_test')
    schema = 'case_' + uuid.uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    db = Store(dsn, schema)
    try:
        db.migrate()
        yield db
    finally:
        db.close()
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))

@pytest.fixture
def clock():
    return lambda: datetime(2026, 11, 18, 7, 30, tzinfo=timezone.utc)

@pytest.fixture
def catalog():
    from nutrition_demo.catalog import Catalog
    def item(i,n,u='g',state='raw',price='1',reference='100'):
        return {'id':i,'name':i,'unit':u,'state':state,'reference_quantity':reference,
                'nutrients':dict(zip(('kcal','protein_g','carbs_g','fat_g'),n)),
                'source':{'status':'synthetic','note':'Hand-derived test fixture'},
                'price':{'usd':price,'quantity':reference,'status':'synthetic'}}
    return Catalog({'ingredients':[item('chicken',[100,10,5,2]),item('rice',[200,5,40,1],'g','dry'),
                                   item('broccoli',[20,2,3,0]),item('yogurt',[100,15,8,1],'serving','packaged',reference='1')],
                    'recipes':[{'id':'curry','name':'synthetic curry','ingredients':[], 'essential_ingredients':['chicken'],
                                'allowed_substitutions':['chicken','rice','broccoli'],'steps':['synthetic'],
                                'equipment':[],'difficulty':[]} ]})

@pytest.fixture
def service(store,catalog,clock):
    from nutrition_demo.service import NutritionService
    return NutritionService(store,catalog,'America/Los_Angeles',clock)

@pytest.fixture
def stocked(service):
    p=service.preview_inventory_change([
        {'ingredient_id':'chicken','quantity':'1000','unit':'g','state':'raw'},
        {'ingredient_id':'rice','quantity':'1000','unit':'g','state':'dry'},
        {'ingredient_id':'broccoli','quantity':'1000','unit':'g','state':'raw'},
        {'ingredient_id':'yogurt','quantity':'10','unit':'serving','state':'packaged'}], 'purchase')
    assert p.ok,p
    assert service.confirm_preview(p.data['id'],'stock').ok
    return service

@pytest.fixture
def prepared(stocked):
    from nutrition_demo.models import BatchOutput,IngredientAllocation
    s=stocked
    p=s.preview_preparation('curry',[
        {'ingredient_id':'chicken','quantity':'800','unit':'g','state':'raw'},
        {'ingredient_id':'rice','quantity':'400','unit':'g','state':'dry'}],
        [BatchOutput('meal',8,[IngredientAllocation('chicken',800,'g'),IngredientAllocation('rice',400,'g')])], '2026-11-17')
    r=s.confirm_preview(p.data['id'],'prepare')
    assert r.ok,r
    return s,r.data['batch_ids'][0]
