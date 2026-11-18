from pathlib import Path
import json
from decimal import Decimal,ROUND_CEILING
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
        return {'recipe_id':recipe_id, 'boxes':boxes, 'instructions':self.customized_instructions(recipe_id,items,boxes), 'items':snapshots, 'total_nutrients':total,
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
        original=set(i['ingredient_id'] for i in recipe['ingredients'])
        if len(ids-original)>1 or not ids <= allowed:
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
                                    'product_url':ref.get('product_url'), 'link_status':ref.get('link_status','missing'),
                                    'packages_needed':int((need/decimal(ref['package_quantity'],positive=True)).to_integral_value(rounding=ROUND_CEILING))
                                    if ref.get('package_quantity') and ref.get('package_unit')==item['unit'] else None})
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


    def customized_instructions(self,recipe_id,items,boxes):
        recipe=self.recipe(recipe_id)
        by_id={i['ingredient_id']:i for i in items}
        def amount(id,divisor=1):
            i=by_id[id]
            return format(decimal(i['quantity'])/divisor,'f')+' '+i['unit']
        def names(ids):return '、'.join(self.ingredient(i)['name'] for i in ids if i in by_id)
        result=['依本次確認配方備料；數量以確認清單為準，依鍋具容量調整分批。']
        if recipe_id=='curry':
            if 'rice' in by_id:result.append('先煮乾米 '+amount('rice')+'，液體依米種與鍋具確認。')
            if 'broccoli' in by_id:result.append('另烤冷凍花椰菜 '+amount('broccoli')+'，依來源流程分開擺放。')
            aromatics=names(['onion','garlic'])
            if aromatics:result.append('先炒 '+aromatics+'；蒜若有使用，最後短炒。')
            result.append('把 '+names(['potato','carrot'])+' 分兩鍋；依確認水量微滾至近熟。')
            if 'chicken' in by_id:result.append('每鍋後下雞胸 '+amount('chicken',2)+'，恢復微滾，以溫度計核對來源熟度。')
            if 'curry_block' in by_id:result.append('關火後每鍋融化咖哩塊 '+amount('curry_block',2)+'，再小火攪拌增稠。')
        elif recipe_id=='nikujaga':
            result+=['依來源冷藏乾醃與切菜；先煮乾米 '+amount('rice')+'。' if 'rice' in by_id else '依來源冷藏乾醃與切菜。',
                     '兩鍋炒香配方中的蔬菜，加入已確認高湯與調味，蔬菜先燉至近熟。']
            if 'pork_loin' in by_id:result.append('每鍋分批後下豬里肌 '+amount('pork_loin',2)+'，依來源測中心熟度並靜置。')
            result.append('必要時另濃縮部分醬汁裹肉，避免為入味而久燉。')
            if 'broccoli' in by_id:result.append('花椰菜 '+amount('broccoli')+' 另外加熱。')
        elif recipe_id=='bbq':
            if 'pork_shoulder' in by_id:result.append('豬肩肉 '+amount('pork_shoulder')+' 依鍋具與來源壓力烹調，洩壓後手撕。')
            if 'bbq_sauce' in by_id:result.append('拌入 BBQ 醬 '+amount('bbq_sauce')+'。')
            result.append('依包裝煮通心粉，瀝乾後拌入已確認配方的奶油、奶類與起司。')
            if 'broccoli' in by_id:result.append('花椰菜 '+amount('broccoli')+' 另烤；含菜與無菜成品分不同批次。')
        elif recipe_id=='rice_pot':
            result.append('分兩鍋依序操作，每鍋使用確認總量的一半。')
            if 'beef' in by_id:result.append('每鍋炒牛肉 '+amount('beef',2)+'，再炒配方中的蔬菜。')
            if 'broth' in by_id:result.append('Cancel，以每鍋高湯 '+amount('broth',2)+' 刮淨鍋底；這是每鍋全部高湯量。')
            if 'rice' in by_id:result.append('鋪上每鍋乾米 '+amount('rice',2)+'，不往下攪拌，確認低於內鍋半滿線。')
            result.append('依來源 High 4 分鐘、自然釋壓 10 分鐘；需核對實際米種、液體與鍋具。')
            if 'canned_chicken' in by_id:result.append('最後拌入瀝乾雞胸，每鍋 '+amount('canned_chicken',2)+'，再依來源加熱測溫。')
            if 'broccoli' in by_id:result.append('另加熱花椰菜 '+amount('broccoli')+'。')
        else:result+=recipe['steps']
        result.append('本次預計 '+str(boxes)+' 盒；做完後確認實際用量、盒數與各批組成。來源時間僅作參考，熟度依來源與實際測量。')
        return result
