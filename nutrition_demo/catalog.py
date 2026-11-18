from pathlib import Path
import json
from decimal import Decimal
from .models import Nutrients, ZERO, decimal
from .nutrition import scale_nutrients, per_box, used_cost, aggregate_cost, validate_targets, checked_quantity

DATA_DIR = Path(__file__).resolve().parent.parent / 'demo_data'


class Catalog:
    def __init__(self, data, manifest=None):
        self.data = data
        self.ingredients = {i['id']: i for i in data['ingredients']}
        self.recipes = {r['id']: r for r in data['recipes']}
        self.manifest = manifest or {}

    @classmethod
    def load(cls, directory=DATA_DIR):
        p=Path(directory)
        return cls(json.loads((p/'catalog.json').read_text()),json.loads((p/'source_manifest.json').read_text()))

    def ingredient(self, ingredient_id):
        if ingredient_id not in self.ingredients:
            raise ValueError('Unknown ingredient; specify product, nutrition label and unit first')
        return self.ingredients[ingredient_id]

    def recipe(self, recipe_id):
        if recipe_id not in self.recipes:
            raise ValueError('Unknown recipe')
        return self.recipes[recipe_id]

    def snapshot(self, item):
        ref = self.ingredient(item['ingredient_id'])
        qty = checked_quantity(item['quantity'],item['unit'],item['state'],ref)
        if ref.get('nutrients') is None:
            raise ValueError('Missing nutrition: clarify brand/label before calculation')
        nutrients=scale_nutrients(Nutrients.from_dict(ref['nutrients']), qty, ref['reference_quantity'])
        price=ref.get('price')
        return {**item, 'quantity':qty, 'nutrients':nutrients,
                'cost':used_cost(price['usd'],qty,price['quantity']) if price else None,
                'source':ref['source'], 'price_source':price, 'name':ref['name']}

    def calculate(self, recipe_id, items, boxes, targets=None):
        self.recipe(recipe_id)
        if len({i['ingredient_id'] for i in items}) != len(items):
            raise ValueError('Duplicate ingredient')
        snapshots=[self.snapshot(i) for i in items]
        total=sum((s['nutrients'] for s in snapshots),ZERO)
        each=per_box(total,boxes)
        return {'recipe_id':recipe_id, 'boxes':boxes, 'items':snapshots, 'total_nutrients':total,
                'nutrients':{k:getattr(each,k) for k in each.__dataclass_fields__},
                'cost':aggregate_cost(s['cost'] for s in snapshots),
                'targets':validate_targets(each,targets) if targets else None,
                'source_statuses': sorted({s['source']['status'] for s in snapshots})}

    def validate_proposal(self, recipe_id, items):
        recipe=self.recipe(recipe_id)
        ids={i['ingredient_id'] for i in items if decimal(i['quantity']) > 0}
        # Essential ingredients cannot be removed. Optional substitutions are explicit, not implicit.
        if not set(recipe['essential_ingredients']) <= ids:
            raise ValueError('Dish identity: essential ingredients missing')
        allowed=set(i['ingredient_id'] for i in recipe['ingredients']) | set(recipe.get('allowed_substitutions',[]))
        if len(ids - allowed)>1 or not ids <= allowed:
            raise ValueError('Unapproved substitution; preserve dish identity')
        for i in items:
            self.snapshot(i)
        return True

    def recommend(self, inventory, profile):
        available={i['ingredient_id']:decimal(i['quantity']) for i in inventory}
        result=[]
        for recipe in self.recipes.values():
            missing=[]
            for item in recipe['ingredients']:
                need=decimal(item['quantity'])-available.get(item['ingredient_id'],Decimal(0))
                if need>0:
                    ref=self.ingredient(item['ingredient_id'])
                    missing.append({**item,'quantity':need,'name':ref['name'],
                                    'product_url':ref.get('product_url'), 'link_status':ref.get('link_status','missing')})
            costs=[]
            for item in recipe['ingredients']:
                ref=self.ingredient(item['ingredient_id']);price=ref.get('price')
                costs.append(used_cost(price['usd'],item['quantity'],price['quantity']) if price else None)
            result.append({**recipe,'shopping':missing,'cost':aggregate_cost(costs),
                           'capacity_note':'容量為參考；請核對現有鍋具與實際分裝。',
                           'known_equipment':profile.get('equipment',[])})
        return sorted(result,key=lambda r:len(r['shopping']))

    def suggest_additions(self, box, targets):
        result=[]
        for ingredient in self.ingredients.values():
            if not ingredient.get('addon_serving') or not ingredient.get('nutrients'):
                continue
            item={'ingredient_id':ingredient['id'],'quantity':ingredient['addon_serving'],
                  'unit':ingredient['unit'],'state':ingredient['state']}
            snapshot=self.snapshot(item)
            whole=box+snapshot['nutrients']
            result.append({'items':[item], 'meal_nutrients':whole,
                           'targets':validate_targets(whole,targets), 'source':snapshot['source']})
        return result
