"""Authoritative domain operations. Models never receive the confirmation capability."""
from collections import defaultdict
from copy import deepcopy
from dataclasses import asdict, is_dataclass
from datetime import datetime, date, timedelta, timezone as utc_timezone
from decimal import Decimal
from functools import wraps
from hashlib import sha256
from uuid import uuid4
from zoneinfo import ZoneInfo
import psycopg
from .models import Result, Nutrients, ZERO, decimal, encode, dumps
from .nutrition import aggregate_cost, per_box, validate_targets, scale_nutrients
from .store import jsonb


def safe(method):
    @wraps(method)
    def run(*args, **kwargs):
        try:
            data=method(*args,**kwargs)
            return data if isinstance(data,Result) else Result(True,data)
        except (ValueError,KeyError,TypeError) as exc:
            message=str(exc) if isinstance(exc,ValueError) else 'Invalid or missing fields'
            return Result(False,{},message)
        except psycopg.Error:
            return Result(False,{},'database_transaction_failed; retry with the same request_id')
    return run


def uid():
    return str(uuid4())


def n(value):
    return value if isinstance(value,Nutrients) else Nutrients.from_dict(value)


class NutritionService:
    def __init__(self,store,catalog,timezone='America/Los_Angeles',clock=None):
        self.store,self.catalog=store,catalog
        self.timezone=ZoneInfo(timezone)
        self.clock=clock or (lambda:datetime.now(utc_timezone.utc))

    def _day(self,value):
        with self.store.transaction() as c:
            row=c.execute('SELECT data FROM profile WHERE id=1').fetchone()
        zone=ZoneInfo(row['data'].get('timezone',str(self.timezone))) if row else self.timezone
        today=self.clock().astimezone(zone).date()
        if value in ('today','今天',None):return today.isoformat()
        if value in ('yesterday','昨天'):return (today-timedelta(days=1)).isoformat()
        try:return date.fromisoformat(value).isoformat()
        except (ValueError,TypeError):raise ValueError('Use an ISO date, today or yesterday') from None

    def _version(self,c):
        return c.execute('SELECT version FROM state_meta WHERE id=1').fetchone()['version']

    def _advance(self,c):
        c.execute('UPDATE state_meta SET version=version+1 WHERE id=1')

    @safe
    def get_profile(self):
        with self.store.transaction() as c:
            row=c.execute('SELECT data FROM profile WHERE id=1').fetchone()
            return row['data'] if row else {'needs_setup':True}

    def _validated_profile(self,c,values):
        row=c.execute('SELECT data FROM profile WHERE id=1').fetchone()
        merged={**(row['data'] if row else {}),**values}
        ZoneInfo(merged['timezone'])
        for field in ('meal_targets','daily_targets'):
            if field not in merged:raise ValueError('Meal and daily targets required separately')
            target=Nutrients.from_dict(merged[field]);validate_targets(target,target)
            merged[field]=target
        if 'container_ml' in merged:merged['container_ml']=decimal(merged['container_ml'],positive=True)
        return encode(merged)

    def _apply_profile(self,c,values):
        merged=self._validated_profile(c,values)
        c.execute('INSERT INTO profile VALUES(1,%s) ON CONFLICT(id) DO UPDATE SET data=excluded.data',(jsonb(merged),))
        return merged

    @safe
    def set_profile(self,values):
        with self.store.transaction(lock=True) as c:
            result=self._apply_profile(c,values)
            self._advance(c)
            return result

    @safe
    def preview_profile(self,values):
        with self.store.transaction(lock=True) as c:
            values=self._validated_profile(c,values)
            return self._preview(c,'profile',values,[{'profile':values}],'確認營養目標、時區與廚具設定後保存。')

    @safe
    def list_inventory(self):
        with self.store.transaction() as c:
            return {'items':c.execute('SELECT * FROM inventory ORDER BY ingredient_id').fetchall()}

    def _items(self,items,*,nutrition=True,c=None):
        catalog=self.effective_catalog(c)
        if not isinstance(items,list):raise ValueError('Items must be a list')
        if len({i['ingredient_id'] for i in items})!=len(items):raise ValueError('Duplicate ingredient')
        result=[]
        for item in items:
            ref=catalog.ingredient(item['ingredient_id'])
            if item['unit']!=ref['unit'] or item['state']!=ref['state']:
                raise ValueError('Unit/state mismatch; clarify density or raw/cooked basis')
            quantity=decimal(item['quantity'])
            if nutrition:
                result.append(encode(catalog.snapshot({**item,'quantity':quantity})))
            else:
                result.append({'ingredient_id':item['ingredient_id'],'quantity':str(quantity),
                               'unit':item['unit'],'state':item['state'],'source':ref['source']})
        return result

    def _stock(self,c,id):
        row=c.execute('SELECT * FROM inventory WHERE ingredient_id=%s',(id,)).fetchone()
        if not row:raise ValueError('Missing inventory: '+id)
        return row

    def _check_stock(self,c,items):
        for item in items:
            row=self._stock(c,item['ingredient_id'])
            if row['unit']!=item['unit'] or row['state']!=item['state']:
                raise ValueError('Inventory unit/state mismatch')
            if row['quantity']<decimal(item['quantity']):
                raise ValueError('needs_clarification: insufficient inventory '+item['ingredient_id'])

    def _preview(self,c,kind,payload,changes,summary):
        id=uid();version=self._version(c)
        data=encode({'payload':payload,'changes':changes,'summary':summary})
        c.execute('INSERT INTO previews(id,kind,state_version,data,created_at) VALUES(%s,%s,%s,%s,%s)',
                  (id,kind,version,jsonb(data),self.clock()))
        return {'id':id,'kind':kind,'state_version':version,'changes':data['changes'],'summary':summary}

    @safe
    def preview_inventory_change(self,items,mode):
        if mode not in ('purchase','reconcile'):raise ValueError('Unknown inventory mode')
        items=self._items(items,nutrition=False)
        if not items:raise ValueError('No inventory changes')
        with self.store.transaction(lock=True) as c:
            changes=[]
            for i in items:
                row=c.execute('SELECT * FROM inventory WHERE ingredient_id=%s',(i['ingredient_id'],)).fetchone()
                old=row['quantity'] if row else Decimal(0)
                if row and (row['unit']!=i['unit'] or row['state']!=i['state']):raise ValueError('Inventory basis mismatch')
                new=old+decimal(i['quantity']) if mode=='purchase' else decimal(i['quantity'])
                changes.append({'ingredient_id':i['ingredient_id'],'before':old,'after':new,'unit':i['unit']})
            return self._preview(c,'inventory',{'items':items,'mode':mode},changes,'確認食材購入／庫存校正後才更新。')

    @safe
    def preview_preparation(self,recipe_id,actual_usage,outputs,prepared_on,confirmed_dispositions=None):
        self.catalog.recipe(recipe_id)
        actual=self._items(actual_usage)
        if not actual:raise ValueError('Actual ingredients required')
        outputs=[asdict(b) if is_dataclass(b) else b for b in outputs]
        if not outputs:raise ValueError('At least one output batch required')
        usage={i['ingredient_id']:i for i in actual}
        allocated=defaultdict(Decimal)
        dispositions=confirmed_dispositions or []
        for b in outputs:
            if not b['name'].strip():raise ValueError('Batch name required')
            per_box(ZERO,b['boxes'])
            if not b['allocations']:raise ValueError('Batch allocation required')
            seen=set()
            for a in b['allocations']:
                id=a['cooking_ingredient_id']
                if id in seen:raise ValueError('Duplicate ingredient allocation in batch')
                seen.add(id)
                if id not in usage or a['unit']!=usage[id]['unit']:raise ValueError('Unknown allocation or unit mismatch')
                allocated[id]+=decimal(a['quantity'],positive=True)
        for a in dispositions:
            id=a['cooking_ingredient_id']
            if a['kind'] not in ('remaining','loss') or id not in usage or a['unit']!=usage[id]['unit']:
                raise ValueError('Invalid disposition or unit mismatch')
            allocated[id]+=decimal(a['quantity'],positive=True)
        if any(allocated[id]!=decimal(i['quantity']) for id,i in usage.items()):
            raise ValueError('Ingredient allocation must conserve total usage exactly')
        with self.store.transaction(lock=True) as c:
            actual=self._items(actual_usage,c=c)
            self._check_stock(c,actual)
            payload={'recipe_id':recipe_id,'actual_usage':actual,'outputs':outputs,
                     'prepared_on':self._day(prepared_on),'dispositions':dispositions}
            changes=[{'ingredient_id':i['ingredient_id'],'consume':i['quantity'],'unit':i['unit']} for i in actual]
            changes+=[{'batch':b['name'],'boxes':b['boxes'],'allocations':b['allocations']} for b in outputs]
            return self._preview(c,'preparation',payload,changes,'一次扣除本次總用量；各批營養與成本只計獲分配食材。')

    def _batch(self,c,batch_id):
        row=c.execute('SELECT * FROM batches WHERE id=%s',(batch_id,)).fetchone()
        if not row:raise ValueError('Unknown batch')
        return row

    def _addons(self,c,batch_id):
        row=c.execute('SELECT version,data FROM batch_addons WHERE batch_id=%s ORDER BY version DESC LIMIT 1',(batch_id,)).fetchone()
        return row if row else {'version':0,'data':{'items':[]}}

    @safe
    def preview_batch_addons(self,batch_id,items):
        items=self._items(items)
        with self.store.transaction(lock=True) as c:
            self._batch(c,batch_id)
            items=self._items(items,c=c)
            version=self._addons(c,batch_id)['version']+1
            return self._preview(c,'addons',{'batch_id':batch_id,'items':items,'version':version},
                                 [{'batch_id':batch_id,'items':items,'version':version}],
                                 '確認每餐預設加餐；食用時才扣庫存，現在不新增攝取。')

    def _move(self,c,item,delta,kind,*,run=None,event=None):
        row=self._stock(c,item['ingredient_id'])
        if row['unit']!=item['unit'] or row['state']!=item['state']:raise ValueError('Inventory basis mismatch')
        delta=Decimal(str(delta))
        if row['quantity']+delta<0:raise ValueError('needs_clarification: insufficient inventory '+item['ingredient_id'])
        c.execute('UPDATE inventory SET quantity=quantity+%s WHERE ingredient_id=%s',(delta,item['ingredient_id']))
        c.execute('INSERT INTO inventory_movements(ingredient_id,delta,cooking_run_id,event_id,kind,data) VALUES(%s,%s,%s,%s,%s,%s)',
                  (item['ingredient_id'],delta,run,event,kind,jsonb({'unit':item['unit'],'snapshot':item})))

    def _apply_inventory(self,c,payload):
        for i in payload['items']:
            row=c.execute('SELECT * FROM inventory WHERE ingredient_id=%s',(i['ingredient_id'],)).fetchone()
            if not row:
                c.execute('INSERT INTO inventory VALUES(%s,0,%s,%s,%s)',(i['ingredient_id'],i['unit'],i['state'],jsonb(i['source'])))
                old=Decimal(0)
            else:old=row['quantity']
            delta=decimal(i['quantity']) if payload['mode']=='purchase' else decimal(i['quantity'])-old
            self._move(c,i,delta,payload['mode'])
        return {'updated_inventory':True}

    def _apply_preparation(self,c,payload,request_id):
        self._check_stock(c,payload['actual_usage'])
        run=uid();mapping={};batch_ids=[]
        c.execute('INSERT INTO cooking_runs VALUES(%s,%s,%s,%s,%s)',
                  (run,payload['recipe_id'],payload['prepared_on'],request_id,jsonb(payload)))
        for i in payload['actual_usage']:
            ingredient=uid();mapping[i['ingredient_id']]=(ingredient,i)
            c.execute('INSERT INTO cooking_ingredients VALUES(%s,%s,%s,%s,%s,%s)',
                      (ingredient,run,i['ingredient_id'],decimal(i['quantity']),i['unit'],jsonb(i)))
            self._move(c,i,-decimal(i['quantity']),'preparation',run=run)
        for output in payload['outputs']:
            id=uid();batch_ids.append(id);total=ZERO;costs=[];sources=[]
            for a in output['allocations']:
                _,i=mapping[a['cooking_ingredient_id']]
                ratio=decimal(a['quantity'])/decimal(i['quantity'],positive=True)
                total+=scale_nutrients(n(i['nutrients']),decimal(a['quantity']),decimal(i['quantity']))
                costs.append(decimal(i['cost'])*decimal(a['quantity'])/decimal(i['quantity']) if i['cost'] is not None else None)
                sources.append(i['source'])
            cost=aggregate_cost(costs)
            data={'box_nutrients':per_box(total,output['boxes']),'total_nutrients':total,
                  'box_cost':{**cost,'known_subtotal':cost['known_subtotal']/output['boxes'],
                              'total':cost['total']/output['boxes'] if cost['complete'] else None},
                  'total_cost':cost,'sources':sources,'recipe_id':payload['recipe_id']}
            c.execute('INSERT INTO batches VALUES(%s,%s,%s,%s,%s,%s)',
                      (id,run,output['name'],output['boxes'],output['boxes'],jsonb(data)))
            for a in output['allocations']:
                c.execute('INSERT INTO batch_ingredients VALUES(%s,%s,%s,%s)',
                          (id,mapping[a['cooking_ingredient_id']][0],decimal(a['quantity']),a['unit']))
        return {'cooking_run_id':run,'batch_ids':batch_ids}

    def _operation(self,c,request_id,inputs,apply):
        if not isinstance(request_id,str) or not request_id.strip():raise ValueError('request_id required')
        digest=sha256(dumps(inputs).encode()).hexdigest()
        prior=c.execute('SELECT input_hash,result FROM operations WHERE request_id=%s',(request_id,)).fetchone()
        if prior:
            if prior['input_hash']!=digest:raise ValueError('request_id reused with different input')
            return prior['result']
        result=encode(apply())
        c.execute('INSERT INTO operations(request_id,input_hash,result) VALUES(%s,%s,%s)',(request_id,digest,jsonb(result)))
        self._advance(c)
        return result

    @safe
    def confirm_preview(self,preview_id,request_id,*,actor='user'):
        if actor!='user':raise ValueError('Only application user input can confirm')
        with self.store.transaction(lock=True) as c:
            def apply():
                p=c.execute('SELECT * FROM previews WHERE id=%s',(preview_id,)).fetchone()
                if not p or p['status']!='pending':raise ValueError('Preview is not pending')
                if p['state_version']!=self._version(c):raise ValueError('Stale preview; regenerate and confirm new changes')
                if (self.clock()-p['created_at']).total_seconds()>1800:raise ValueError('Expired preview; regenerate')
                payload=p['data']['payload'];kind=p['kind']
                if kind=='product_label':result=self._apply_product_label(c,payload)
                elif kind=='profile':result=self._apply_profile(c,payload)
                elif kind=='inventory':result=self._apply_inventory(c,payload)
                elif kind=='preparation':result=self._apply_preparation(c,payload,request_id)
                elif kind=='addons':
                    c.execute('INSERT INTO batch_addons VALUES(%s,%s,%s)',(payload['batch_id'],payload['version'],jsonb({'items':payload['items']})))
                    result={'batch_id':payload['batch_id'],'addon_version':payload['version']}
                elif kind=='correction':result=self._apply_correction(c,payload)
                elif kind=='reconciled_meal':
                    self._apply_inventory(c,payload['inventory'])
                    result=self._apply_meal(c,payload['meal'])
                else:raise ValueError('Unknown preview type')
                c.execute("UPDATE previews SET status='confirmed',confirmed_at=%s WHERE id=%s",(self.clock(),preview_id))
                return result
            return self._operation(c,request_id,{'confirm_preview':preview_id},apply)

    @safe
    def reject_preview(self,preview_id):
        with self.store.transaction(lock=True) as c:
            row=c.execute("UPDATE previews SET status='rejected' WHERE id=%s AND status='pending' RETURNING id",(preview_id,)).fetchone()
            if not row:raise ValueError('Preview is not pending')
            return {'rejected':preview_id}

    @safe
    def find_batches(self,query):
        with self.store.transaction() as c:
            rows=c.execute('SELECT id,name,remaining_boxes FROM batches WHERE remaining_boxes>0 AND (id=%s OR name ILIKE %s) ORDER BY id',
                           (query,'%'+query+'%')).fetchall()
            return {'candidates':rows,'needs_clarification':len(rows)!=1}

    @safe
    def batch_summary(self):
        with self.store.transaction() as c:
            batches=[]
            for b in c.execute('SELECT * FROM batches ORDER BY cooking_run_id,name').fetchall():
                addons=self._addons(c,b['id']);box=n(b['data']['box_nutrients'])
                addon_total=sum((n(i['nutrients']) for i in addons['data']['items']),ZERO)
                cost=b['data']['box_cost']
                batches.append({'id':b['id'],'name':b['name'],'cooking_run_id':b['cooking_run_id'],
                                'remaining_boxes':b['remaining_boxes'],'total_boxes':b['total_boxes'],
                                'box_nutrients':asdict(box),'default_addons':addons['data']['items'],
                                'addon_version':addons['version'],'meal_nutrients':asdict(box+addon_total),
                                'box_cost':{**cost,'known_subtotal':decimal(cost['known_subtotal']),
                                            'total':decimal(cost['total']) if cost['total'] is not None else None},
                                'sources':b['data']['sources']})
            return {'batches':batches}

    def _meal_payload(self,c,batch_id,eaten_on,meal=None,addon_override=None,*,check_stock=True):
        b=self._batch(c,batch_id)
        if b['remaining_boxes']<=0:raise ValueError('No boxes remaining')
        addons=self._addons(c,batch_id)
        items=addons['data']['items'] if addon_override is None else self._items(addon_override,c=c)
        if check_stock:self._check_stock(c,items)
        box=n(b['data']['box_nutrients']);extra=sum((n(i['nutrients']) for i in items),ZERO)
        return encode({'batch_id':batch_id,'batch_name':b['name'],'eaten_on':self._day(eaten_on),'meal':meal,
                       'box_nutrients':box,'addon_items':items,'addon_nutrients':extra,
                       'total_nutrients':box+extra,'addon_version':addons['version'],
                       'box_sources':b['data']['sources']})

    def _apply_meal(self,c,payload):
        b=self._batch(c,payload['batch_id'])
        if b['remaining_boxes']<=0:raise ValueError('No boxes remaining')
        self._check_stock(c,payload['addon_items'])
        event=uid()
        c.execute('INSERT INTO events(id,batch_id,eaten_on,meal,data) VALUES(%s,%s,%s,%s,%s)',
                  (event,payload['batch_id'],payload['eaten_on'],payload['meal'],jsonb(payload)))
        c.execute('UPDATE batches SET remaining_boxes=remaining_boxes-1 WHERE id=%s',(payload['batch_id'],))
        for i in payload['addon_items']:self._move(c,i,-decimal(i['quantity']),'meal_addon',event=event)
        return {'event_id':event,**payload}

    @safe
    def log_meal(self,batch_id,eaten_on,meal,request_id,addon_override=None):
        with self.store.transaction(lock=True) as c:
            return self._operation(c,request_id,{'log_meal':{'batch_id':batch_id,'eaten_on':eaten_on,'meal':meal,'addon_override':addon_override}},
                lambda:self._apply_meal(c,self._meal_payload(c,batch_id,eaten_on,meal,addon_override)))

    @safe
    def preview_reconciled_meal(self,items,meal_input,mode='reconcile'):
        if mode not in ('purchase','reconcile'):raise ValueError('Unknown inventory mode')
        items=self._items(items,nutrition=False)
        with self.store.transaction(lock=True) as c:
            payload=self._meal_payload(c,**meal_input,check_stock=False)
            overrides={i['ingredient_id']:i for i in items}
            changes=[]
            for i in payload['addon_items']:
                row=c.execute('SELECT * FROM inventory WHERE ingredient_id=%s',(i['ingredient_id'],)).fetchone()
                available=row['quantity'] if row else Decimal(0)
                if row and (row['unit']!=i['unit'] or row['state']!=i['state']):raise ValueError('Inventory basis mismatch')
                if i['ingredient_id'] in overrides:
                    x=overrides[i['ingredient_id']]
                    available=available+decimal(x['quantity']) if mode=='purchase' else decimal(x['quantity'])
                if available<decimal(i['quantity']):raise ValueError('needs_clarification: still insufficient inventory')
            for i in items:
                row=c.execute('SELECT * FROM inventory WHERE ingredient_id=%s',(i['ingredient_id'],)).fetchone()
                old=row['quantity'] if row else Decimal(0)
                new=old+decimal(i['quantity']) if mode=='purchase' else decimal(i['quantity'])
                changes.append({'ingredient_id':i['ingredient_id'],'before':old,'after_inventory_adjustment':new,'unit':i['unit']})
            changes.append({'meal_to_record':payload})
            return self._preview(c,'reconciled_meal',{'inventory':{'items':items,'mode':mode},'meal':payload},changes,
                                 '確認庫存差異與實際食用後，一次更新兩者。')

    @safe
    def daily_summary(self,day):
        day=self._day(day)
        with self.store.transaction() as c:
            rows=c.execute('SELECT data FROM events WHERE eaten_on=%s ORDER BY id',(day,)).fetchall()
            box=sum((n(r['data']['box_nutrients']) for r in rows),ZERO)
            extra=sum((n(r['data']['addon_nutrients']) for r in rows),ZERO)
            profile=c.execute('SELECT data FROM profile WHERE id=1').fetchone()
            targets=profile['data'].get('daily_targets') if profile else None
            total=box+extra
            # Daily progress is not a meal-tolerance acceptance decision.
            progress={k:{'actual':getattr(total,k),'target':decimal(targets[k]),
                         'difference':getattr(total,k)-decimal(targets[k]),
                         'ratio':getattr(total,k)/decimal(targets[k],positive=True)} for k in targets} if targets else None
            return {'day':day,'scope':'recorded_prepared_meals_only','events':len(rows),
                    'box':asdict(box),'addons':asdict(extra),'total':asdict(total),
                    'daily_targets':targets,'progress':progress,'needs_daily_target':targets is None}

    @safe
    def find_events(self,query):
        allowed={'date','batch_id','meal','event_id'}
        if set(query)-allowed:raise ValueError('Unknown event search fields')
        with self.store.transaction() as c:
            rows=c.execute('SELECT * FROM events ORDER BY eaten_on,id').fetchall()
            day=self._day(query['date']) if 'date' in query else None
            rows=[r for r in rows if (not day or r['eaten_on'].isoformat()==day)
                  and ('batch_id' not in query or r['batch_id']==query['batch_id'])
                  and ('meal' not in query or r['meal']==query['meal'])
                  and ('event_id' not in query or r['id']==query['event_id'])]
            return {'candidates':encode(rows),'needs_clarification':len(rows)!=1}

    def _event(self,c,event_id):
        row=c.execute('SELECT * FROM events WHERE id=%s',(event_id,)).fetchone()
        if not row:raise ValueError('Unknown event; search and clarify event identity')
        return row

    def _addon_deltas(self,old,new):
        totals=defaultdict(Decimal);snapshots={}
        for sign,items in ((1,old),(-1,new)):
            for i in items:
                id=i['ingredient_id'];snapshots[id]=i
                totals[id]+=sign*decimal(i['quantity'])
        return [{'item':snapshots[id],'delta':delta} for id,delta in totals.items() if delta]

    @safe
    def preview_correction(self,event_id,changes):
        if not changes or set(changes)-{'date','meal','batch_id','addon_override'}:
            raise ValueError('No correction or unsupported fields')
        with self.store.transaction(lock=True) as c:
            event=self._event(c,event_id);old=event['data'];new=dict(old)
            if 'date' in changes:new['eaten_on']=self._day(changes['date'])
            if 'meal' in changes:new['meal']=changes['meal']
            changing_batch='batch_id' in changes and changes['batch_id']!=old['batch_id']
            if changing_batch:
                b=self._batch(c,changes['batch_id'])
                if b['remaining_boxes']<=0:raise ValueError('No boxes remaining in target batch')
                new.update({'batch_id':b['id'],'batch_name':b['name'],
                            'box_nutrients':b['data']['box_nutrients'],'box_sources':b['data']['sources']})
                plan=self._addons(c,b['id'])
                new.update({'addon_items':plan['data']['items'],'addon_version':plan['version']})
            if 'addon_override' in changes:
                if changes['addon_override'] is None:
                    plan=self._addons(c,new['batch_id'])
                    new.update({'addon_items':plan['data']['items'],'addon_version':plan['version']})
                else:new['addon_items']=self._items(changes['addon_override'],c=c)
            new['addon_nutrients']=encode(sum((n(i['nutrients']) for i in new['addon_items']),ZERO))
            new['total_nutrients']=encode(n(new['box_nutrients'])+n(new['addon_nutrients']))
            if new==old:raise ValueError('No changes to event')
            deltas=self._addon_deltas(old['addon_items'],new['addon_items'])
            for d in deltas:
                row=self._stock(c,d['item']['ingredient_id'])
                if row['quantity']+d['delta']<0:raise ValueError('needs_clarification: insufficient corrected addon inventory')
            detail=[{'before_event':old,'after_event':new}]
            if changing_batch:detail.append({'restore_box_to':old['batch_id'],'consume_box_from':new['batch_id']})
            detail += [{'ingredient_id':d['item']['ingredient_id'],'inventory_delta':d['delta'],
                        'unit':d['item']['unit']} for d in deltas]
            return self._preview(c,'correction',{'event_id':event_id,'old':old,'new':new,'inventory_deltas':deltas},
                                 detail,'核對日期、餐點、加餐、營養與庫存差額後，再確認更正。')

    def _apply_correction(self,c,payload):
        event=self._event(c,payload['event_id']);old=payload['old'];new=payload['new']
        if event['data']!=old:raise ValueError('Event changed; regenerate preview')
        if old['batch_id']!=new['batch_id']:
            b=self._batch(c,new['batch_id'])
            if b['remaining_boxes']<=0:raise ValueError('No boxes remaining in target batch')
            c.execute('UPDATE batches SET remaining_boxes=remaining_boxes+1 WHERE id=%s',(old['batch_id'],))
            c.execute('UPDATE batches SET remaining_boxes=remaining_boxes-1 WHERE id=%s',(new['batch_id'],))
        for d in payload['inventory_deltas']:
            self._move(c,d['item'],d['delta'],'correction',event=event['id'])
        new={**new,'history':old.get('history',[])+[{'snapshot':{k:v for k,v in old.items() if k!='history'},'corrected_at':self.clock()}]}
        c.execute('UPDATE events SET batch_id=%s,eaten_on=%s,meal=%s,data=%s WHERE id=%s',
                  (new['batch_id'],new['eaten_on'],new['meal'],jsonb(new),event['id']))
        return {'event_id':event['id'],'event':new}


    def effective_catalog(self,c=None):
        from .catalog import Catalog
        if c is None:
            with self.store.transaction() as conn:return self.effective_catalog(conn)
        data=deepcopy(self.catalog.data)
        overrides={r['ingredient_id']:r['data'].get('product_label') for r in c.execute('SELECT ingredient_id,data FROM inventory').fetchall()}
        for item in data['ingredients']:
            if overrides.get(item['id']):item.update(overrides[item['id']])
        return Catalog(data,self.catalog.manifest)

    @safe
    def preview_product_label(self,ingredient_id,values):
        self.catalog.ingredient(ingredient_id)
        if set(values)-{'reference_quantity','nutrients','source_note','source_url','price'}:
            raise ValueError('Unknown product label fields')
        reference=decimal(values['reference_quantity'],positive=True)
        nutrients=Nutrients.from_dict(values['nutrients'])
        if not values.get('source_note','').strip():raise ValueError('Label provenance required')
        price=values.get('price')
        if price is not None:
            price={'usd':decimal(price['usd']),'quantity':decimal(price['quantity'],positive=True),
                   'currency':'USD','basis':'user_confirmed_package','checked_on':self._day('today')}
        label={'reference_quantity':reference,'nutrients':nutrients,'price':price,
               'source':{'status':'user_label_confirmed','note':values['source_note'],
                         'url':values.get('source_url'),'checked_on':self._day('today')}}
        with self.store.transaction(lock=True) as c:
            return self._preview(c,'product_label',{'ingredient_id':ingredient_id,'label':label},
                                 [{'ingredient_id':ingredient_id,'label':label}],
                                 '確認實際商品標示與計價基準；只影響後續計算，歷史事件保留原快照。')

    def _apply_product_label(self,c,payload):
        ref=self.catalog.ingredient(payload['ingredient_id'])
        c.execute('INSERT INTO inventory(ingredient_id,quantity,unit,state,data) VALUES(%s,0,%s,%s,%s) '
                  "ON CONFLICT(ingredient_id) DO UPDATE SET data=jsonb_set(inventory.data,'{product_label}',excluded.data->'product_label')",
                  (ref['id'],ref['unit'],ref['state'],jsonb({'product_label':payload['label']})))
        return {'ingredient_id':ref['id'],'label_updated':True}
