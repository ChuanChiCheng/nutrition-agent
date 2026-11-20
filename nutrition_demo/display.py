"""Human-facing terminal presentation; detailed traces stay in PostgreSQL."""
from decimal import Decimal
from .models import encode


def number(v):
    if v is None:return 'unknown'
    try:return format(Decimal(str(v)).quantize(Decimal('0.01')),'f').rstrip('0').rstrip('.')
    except Exception:return str(v)


def nutrients(n):
    n=encode(n)
    return f"{number(n['kcal'])} kcal | Protein {number(n['protein_g'])} g | Carbohydrates {number(n['carbs_g'])} g | Fat {number(n['fat_g'])} g"


def items(values):
    return '\n'.join(f"  • {i.get('name',i.get('ingredient_id',''))}: {number(i['quantity'])} {i['unit']}({i.get('state','')})" for i in values) or '  None'


def cost(c):
    if c.get('complete'):return 'US$'+number(c['total'])
    return 'Known subtotal US$'+number(c['known_subtotal'])+'; some costs remain unknown'


def preview(data):
    lines=[data.get('summary','Review the proposed changes.')]
    for change in data.get('changes',[]):
        if 'before_event' in change:
            old,new=change['before_event'],change['after_event']
            lines += [f"  Original record: {old['eaten_on']} {old.get('meal') or ''}, {old['batch_name']}, {nutrients(old['total_nutrients'])}",
                      f"  Corrected: {new['eaten_on']} {new.get('meal') or ''}, {new['batch_name']}, {nutrients(new['total_nutrients'])}",
                      '  Original addons: \n'+items(old['addon_items']),'  Corrected addons: \n'+items(new['addon_items'])]
        elif 'inventory_delta' in change:
            lines.append(f"  {change['ingredient_id']} Inventory difference: {number(change['inventory_delta'])} {change['unit']}")
        elif 'before' in change:
            lines.append(f"  {change['ingredient_id']}: {number(change['before'])} → {number(change.get('after',change.get('after_inventory_adjustment')))} {change['unit']}")
        elif 'consume' in change:
            lines.append(f"  Ingredient usage: {change['ingredient_id']} {number(change['consume'])} {change['unit']}")
        elif 'batch' in change:
            lines.append(f"  {change['batch']}: {change['boxes']} boxes")
            lines += [f"    {a['cooking_ingredient_id']}: {number(a['quantity'])} {a['unit']}" for a in change['allocations']]
            lines += ['  Per box: '+nutrients(change['box_nutrients']),'  Cost per box: '+cost(change['box_cost'])]
            if change.get('targets'):
                lines.append('  Four nutrient targets: '+('Pass' if change['targets']['passed'] else 'Not all pass'))
                lines += [f"    {k} Difference: {number(v['difference'])}" for k,v in change['targets']['metrics'].items()]
        elif 'items' in change:lines.append('  Default addons (consumed only when eaten): \n'+items(change['items']))
        elif 'profile' in change:
            p=change['profile'];lines+=['  Meal targets: '+nutrients(p['meal_targets']),'  Daily targets: '+nutrients(p['daily_targets']),
                                      '  Timezone: '+p['timezone'],'  Equipment: '+', '.join(p.get('equipment',[])),
                                      '  Reference container capacity: '+number(p.get('container_ml'))+' ml']
        elif 'label' in change:
            label=change['label'];lines.append(f"  {change['ingredient_id']} per {number(label['reference_quantity'])} reference units: {nutrients(label['nutrients'])}")
            lines.append('  Source: '+str(label['source']))
            if label.get('price'):
                lines.append('  Package price: US$'+number(label['price']['usd'])+' / '+number(label['price']['quantity'])+' reference units')
        elif 'meal_to_record' in change:
            m=change['meal_to_record'];lines.append('  Consumption: '+m['batch_name']+' | '+m['eaten_on']+' | '+nutrients(m['total_nutrients']))
        elif 'disposition' in change:
            d=change['disposition'];lines.append('  '+('Remaining' if d['kind']=='remaining' else 'Loss')+': '+d['cooking_ingredient_id']+' '+number(d['quantity'])+' '+d['unit'])
        elif 'restore_box_to' in change:
            lines.append('  Restore one box to the original batch and consume one from the new batch.')
    lines += ['Preview ID: '+data['id'],'Confirm: /confirm '+data['id'],'Reject: /reject '+data['id']]
    return '\n'.join(lines)


def recipe(r):
    lines=[r['name']+'('+r['id']+')','Notes: '+'; '.join(r.get('difficulty',[])),
           'Equipment: '+', '.join(r.get('equipment',[])),'Ingredients: \n'+items(r.get('ingredients',[]))]
    if r.get('unquantified'):lines.append('To verify: '+'; '.join(r['unquantified']))
    lines += [f"  {i+1}. {s}" for i,s in enumerate(r.get('steps',[]))]
    if 'cost' in r:lines.append('Batch cost: '+cost(r['cost']))
    if 'shopping' in r:
        lines.append('Shopping needed: \n'+items(r['shopping']))
        for i in r['shopping']:
            if i.get('product_url'):lines.append('  '+i['name']+'(requires '+str(i.get('packages_needed') or 'to confirm')+' packages): '+i['product_url'])
        lines.append('Product pages do not establish local availability or prices; unverified items have no fabricated links.')
    return '\n'.join(lines)


def data_lines(data):
    if 'explanation' in data:
        answer=data['explanation'];lines=[answer['recipe_name']+' | Explanation with source evidence']
        for evidence in answer['evidence']:
            label='Source page '+str(evidence['page'])+'' if evidence['page'] else 'Current recipe step'
            lines += [label+'('+evidence['id']+'): ',evidence['text']]
        lines.append('When historical source quantities differ, use the current confirmed ingredient list.')
        return lines
    if 'inventory' in data:return data_lines(data['inventory'])
    if 'selected_recipe' in data:return ['Selected recipe: '+data['selected_recipe']+'; next adjust portions and ingredient quantities.']
    if 'rejected' in data:return ['Preview rejected. Inventory and meal records remain unchanged.']
    if 'kind' in data and 'changes' in data:return [preview(data)]
    if 'calculation' in data:
        c=data['calculation'];lines=['Recipe('+str(c['boxes'])+' boxes): \n'+items(data['items']),'Per box: '+nutrients(c['nutrients']),'Batch cost: '+cost(c['cost'])]
        for k,v in c['targets']['metrics'].items():
            lines.append(f"  {k}: {number(v['actual'])}; Range {number(v['lower'])}–{number(v['upper'])}; Difference {number(v['difference'])}; "+('Pass' if v['passed'] else 'Fail'))
        lines.append('Source status: '+', '.join(c['source_statuses']))
        lines.append('Current cooking steps: ')
        lines += [f'  {i+1}. {step}' for i,step in enumerate(c.get('instructions',[]))]
        return lines
    if 'suggestions' in data:
        result=['Addon suggestions (no intake recorded or stock consumed): ']
        for suggestion in data['suggestions']:
            result+=['Suggested addons: \n'+items(suggestion['items']),'Whole meal: '+nutrients(suggestion['meal_nutrients'])]
            for k,v in suggestion['targets']['metrics'].items():
                result.append(f"  {k}: {number(v['actual'])}; Difference {number(v['difference'])}; "+('Pass' if v['passed'] else 'Fail'))
        return result
    if 'items' in data:return ['Ingredient inventory: \n'+items(data['items'])]
    if 'recipes' in data:return [recipe(r) for r in data['recipes']]
    if 'recipe' in data:return [recipe(data['recipe'])]
    if 'batches' in data:
        return [f"{b['name']} | Remaining {b['remaining_boxes']}/{b['total_boxes']} boxes\n  Batch: {b['id']}\n  Box contents: {nutrients(b['box_nutrients'])}\n  Default whole meal: {nutrients(b['meal_nutrients'])}\n  Cost per box: {cost(b['box_cost'])}\n  Default addons: \n{items(b['default_addons'])}" for b in data['batches']] or ['No prepared batches are available.']
    if 'scope' in data:
        lines=[f"{data['day']} | Recorded prepared meals {data['events']} meals",'Box contents: '+nutrients(data['box']),
                'Actual addons: '+nutrients(data['addons']),'Total: '+nutrients(data['total']),
                'Daily targets: '+nutrients(data['daily_targets']) if data.get('daily_targets') else 'Daily targets are not configured.',
                'Includes only recorded prepared meals; excludes restaurant meals, drinks, and other snacks.']
        labels={'kcal':'Calories','protein_g':'Protein','carbs_g':'Carbohydrates','fat_g':'Fat'}
        for key,value in (data.get('progress') or {}).items():
            percent=Decimal(str(value['ratio']))*100
            lines.append(f"  {labels.get(key,key)}: {number(value['actual'])} / {number(value['target'])}({number(percent)}%); Difference {number(value['difference'])}")
        return lines
    if 'candidates' in data:
        return ['Candidates: ']+[f"  {x['id']} | {x.get('name',x.get('data',{}).get('batch_name',''))} | {x.get('eaten_on',x.get('remaining_boxes',''))}" for x in data['candidates']]+(['Select one candidate first.'] if data.get('needs_clarification') else [])
    if 'event_id' in data:
        lines=['Meal record updated: '+data['event_id']]
        for key,label in (('batch_name','Batch'),('eaten_on','Date'),('meal','Meal')):
            if data.get(key) is not None:lines.append(label+': '+data[key])
        if 'total_nutrients' in data:lines.append('This meal: '+nutrients(data['total_nutrients']))
        return lines
    if 'batch_ids' in data:return ['Preparation confirmed; ingredients were consumed once.','Batch: '+', '.join(data['batch_ids'])]
    if 'updated_inventory' in data:return ['Inventory updated.']
    if 'addon_version' in data:return ['Default addon plan saved; no intake recorded or stock consumed.']
    if 'label_updated' in data:return ['Product label saved for future calculations; existing snapshots are preserved.']
    if 'meal_targets' in data:return ['Meal targets: '+nutrients(data['meal_targets']),'Daily targets: '+nutrients(data['daily_targets']),'Timezone: '+data['timezone']]
    if data.get('needs_setup'):return ['Profile is not configured. Provide timezone, equipment, and separate meal and daily targets.']
    return []


def render(result):
    lines=[]
    if result.error:lines.append('Operation did not complete: '+result.error)
    if result.data.get('message'):lines.append(result.data['message'])
    if 'tool_results' in result.data:
        for record in result.data['tool_results']:
            r=record['result']
            if r['ok']:lines+=data_lines(r['data'])
            else:lines.append('Action needed: '+str(r['error']))
    else:lines+=data_lines(result.data)
    return '\n\n'.join(lines) or ('Completed.' if result.ok else 'Provide missing details and retry.')
