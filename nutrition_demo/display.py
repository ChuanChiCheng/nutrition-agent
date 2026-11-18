"""Human-facing terminal presentation; detailed traces stay in PostgreSQL."""
from decimal import Decimal
from .models import encode


def number(v):
    if v is None:return '未知'
    try:return format(Decimal(str(v)).quantize(Decimal('0.01')),'f').rstrip('0').rstrip('.')
    except Exception:return str(v)


def nutrients(n):
    n=encode(n)
    return f"{number(n['kcal'])} kcal｜蛋白質 {number(n['protein_g'])} g｜碳水 {number(n['carbs_g'])} g｜脂肪 {number(n['fat_g'])} g"


def items(values):
    return '\n'.join(f"  • {i.get('name',i.get('ingredient_id',''))}：{number(i['quantity'])} {i['unit']}（{i.get('state','')}）" for i in values) or '  無'


def cost(c):
    if c.get('complete'):return 'US$'+number(c['total'])
    return '已知小計 US$'+number(c['known_subtotal'])+'；尚有未知成本'


def preview(data):
    lines=[data.get('summary','請核對變更內容。')]
    for change in data.get('changes',[]):
        if 'before_event' in change:
            old,new=change['before_event'],change['after_event']
            lines += [f"  原紀錄：{old['eaten_on']} {old.get('meal') or ''}，{old['batch_name']}，{nutrients(old['total_nutrients'])}",
                      f"  更正後：{new['eaten_on']} {new.get('meal') or ''}，{new['batch_name']}，{nutrients(new['total_nutrients'])}",
                      '  原加餐：\n'+items(old['addon_items']),'  更正後加餐：\n'+items(new['addon_items'])]
        elif 'inventory_delta' in change:
            lines.append(f"  {change['ingredient_id']} 庫存差額：{number(change['inventory_delta'])} {change['unit']}")
        elif 'before' in change:
            lines.append(f"  {change['ingredient_id']}：{number(change['before'])} → {number(change.get('after',change.get('after_inventory_adjustment')))} {change['unit']}")
        elif 'consume' in change:
            lines.append(f"  原料消耗：{change['ingredient_id']} {number(change['consume'])} {change['unit']}")
        elif 'batch' in change:
            lines.append(f"  {change['batch']}：{change['boxes']} 盒")
            lines += [f"    {a['cooking_ingredient_id']}：{number(a['quantity'])} {a['unit']}" for a in change['allocations']]
        elif 'items' in change:lines.append('  預設加餐（食用時才扣除）：\n'+items(change['items']))
        elif 'profile' in change:
            p=change['profile'];lines+=['  每餐目標：'+nutrients(p['meal_targets']),'  每日目標：'+nutrients(p['daily_targets']),
                                      '  時區：'+p['timezone'],'  廚具：'+', '.join(p.get('equipment',[]))]
        elif 'label' in change:
            label=change['label'];lines.append(f"  {change['ingredient_id']} 每 {number(label['reference_quantity'])} 原單位：{nutrients(label['nutrients'])}")
            lines.append('  來源：'+str(label['source']))
        elif 'meal_to_record' in change:
            m=change['meal_to_record'];lines.append('  食用：'+m['batch_name']+'｜'+m['eaten_on']+'｜'+nutrients(m['total_nutrients']))
        elif 'restore_box_to' in change:
            lines.append('  歸還原批次一盒，扣除新批次一盒。')
    lines += ['預覽編號：'+data['id'],'確認：/confirm '+data['id'],'拒絕：/reject '+data['id']]
    return '\n'.join(lines)


def recipe(r):
    lines=[r['name']+'（'+r['id']+'）','需要注意：'+'；'.join(r.get('difficulty',[])),
           '器具：'+'、'.join(r.get('equipment',[])),'食材：\n'+items(r.get('ingredients',[]))]
    if r.get('unquantified'):lines.append('待核對：'+'；'.join(r['unquantified']))
    lines += [f"  {i+1}. {s}" for i,s in enumerate(r.get('steps',[]))]
    if 'cost' in r:lines.append('整批成本：'+cost(r['cost']))
    if 'shopping' in r:
        lines.append('需要補買：\n'+items(r['shopping']))
        for i in r['shopping']:
            if i.get('product_url'):lines.append('  '+i['name']+'（需 '+str(i.get('packages_needed') or '待確認')+' 包）：'+i['product_url'])
        lines.append('商品頁未表示當地庫存或價格；未核對的品項不提供假連結。')
    return '\n'.join(lines)


def data_lines(data):
    if 'inventory' in data:return data_lines(data['inventory'])
    if 'selected_recipe' in data:return ['已選料理：'+data['selected_recipe']+'；接著可調整餐數與食材用量。']
    if 'rejected' in data:return ['預覽已拒絕，庫存與食用紀錄未更動。']
    if 'kind' in data and 'changes' in data:return [preview(data)]
    if 'items' in data:return ['食材庫存：\n'+items(data['items'])]
    if 'recipes' in data:return [recipe(r) for r in data['recipes']]
    if 'recipe' in data:return [recipe(data['recipe'])]
    if 'batches' in data:
        return [f"{b['name']}｜剩 {b['remaining_boxes']}/{b['total_boxes']} 盒\n  批次：{b['id']}\n  盒內：{nutrients(b['box_nutrients'])}\n  預設整餐：{nutrients(b['meal_nutrients'])}\n  每盒成本：{cost(b['box_cost'])}\n  預設加餐：\n{items(b['default_addons'])}" for b in data['batches']] or ['目前沒有完成的備餐。']
    if 'scope' in data:
        return [f"{data['day']}｜已記錄備餐 {data['events']} 餐",'盒內：'+nutrients(data['box']),
                '實際加餐：'+nutrients(data['addons']),'合計：'+nutrients(data['total']),
                '每日目標：'+nutrients(data['daily_targets']) if data.get('daily_targets') else '每日目標尚未設定。',
                '僅包含已記錄備餐；未包含外食、飲料或其他零食。']
    if 'candidates' in data:
        return ['候選資料：']+[f"  {x['id']}｜{x.get('name',x.get('data',{}).get('batch_name',''))}｜{x.get('eaten_on',x.get('remaining_boxes',''))}" for x in data['candidates']]+(['請先選定一筆。'] if data.get('needs_clarification') else [])
    if 'event_id' in data:return ['飲食紀錄已更新：'+data['event_id']]+(['本餐：'+nutrients(data['total_nutrients'])] if 'total_nutrients' in data else [])
    if 'batch_ids' in data:return ['烹調已確認；本次原料已扣除一次。','批次：'+', '.join(data['batch_ids'])]
    if 'updated_inventory' in data:return ['庫存已更新。']
    if 'addon_version' in data:return ['預設加餐方案已保存；尚未新增攝取或扣料。']
    if 'label_updated' in data:return ['商品標示已保存，後續計算會優先採用；既有快照保留。']
    if 'calculation' in data:
        c=data['calculation'];lines=['配方（'+str(c['boxes'])+' 盒）：\n'+items(data['items']),'每盒：'+nutrients(c['nutrients']),'整批成本：'+cost(c['cost'])]
        for k,v in c['targets']['metrics'].items():
            lines.append(f"  {k}：{number(v['actual'])}；範圍 {number(v['lower'])}–{number(v['upper'])}；差距 {number(v['difference'])}；"+('通過' if v['passed'] else '未通過'))
        lines.append('來源狀態：'+', '.join(c['source_statuses']))
        lines.append('本次操作步驟：')
        lines += [f'  {i+1}. {step}' for i,step in enumerate(c.get('instructions',[]))]
        return lines
    if 'meal_targets' in data:return ['每餐目標：'+nutrients(data['meal_targets']),'每日目標：'+nutrients(data['daily_targets']),'時區：'+data['timezone']]
    if data.get('needs_setup'):return ['尚未設定個人目標、時區與廚具；請分別提供每餐與每日目標。']
    return []


def render(result):
    lines=[]
    if result.error:lines.append('操作未完成：'+result.error)
    if result.data.get('message'):lines.append(result.data['message'])
    if 'tool_results' in result.data:
        for record in result.data['tool_results']:
            r=record['result']
            if r['ok']:lines+=data_lines(r['data'])
            else:lines.append('需要處理：'+str(r['error']))
    else:lines+=data_lines(result.data)
    return '\n\n'.join(lines) or ('已完成。' if result.ok else '請補充資料後重試。')
