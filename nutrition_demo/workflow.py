from uuid import uuid4
from .models import Result, Nutrients, encode
from .store import jsonb
from .nutrition import validate_targets


class Workflow:
    def __init__(self,service,session_id='interactive'):
        self.service,self.store,self.session_id=service,service.store,session_id

    def load(self):
        with self.store.transaction() as c:
            row=c.execute('SELECT data FROM workflow_sessions WHERE id=%s',(self.session_id,)).fetchone()
            return row['data'] if row else {'stage':'inventory_confirmation','inventory_confirmed':False,
                                            'selected_recipe':None,'proposal':None,'attempts':0,
                                            'pending_preview':None,'waiting_question':None,'clarifications':0,
                                            'history':[]}

    def save(self,state):
        with self.store.transaction(lock=True) as c:
            c.execute('INSERT INTO workflow_sessions(id,data) VALUES(%s,%s) ON CONFLICT(id) DO UPDATE SET data=excluded.data,updated_at=CURRENT_TIMESTAMP',
                      (self.session_id,jsonb(state)))

    def command(self,message):
        parts=message.split();cmd=parts[0] if parts else '';state=self.load()
        if cmd=='/inventory-ok':
            state.update(inventory_confirmed=True,stage='recipe_selection',waiting_question=None)
            result=Result(True,{'inventory_confirmed':True,'message':'Inventory confirmed. Select a recipe.'})
        elif cmd=='/select' and len(parts)==2:
            if not state['inventory_confirmed']:return Result(False,{},'Confirm current inventory before selecting recipe')
            try:self.service.catalog.recipe(parts[1])
            except ValueError as e:return Result(False,{},str(e))
            state.update(selected_recipe=parts[1],stage='customization',attempts=0,proposal=None,accepted_recipe=None)
            result=Result(True,{'selected_recipe':parts[1]})
        elif cmd=='/accept-recipe' and len(parts) in (2,3):
            p=state['proposal']
            if not p or p['id']!=parts[1]:return Result(False,{},'Select a current calculated proposal')
            if not p['calculation']['targets']['passed'] and parts[2:]!=['outside']:
                return Result(False,{},'Outside targets; explicitly accept with outside to retain unmet status')
            state.update(stage='cooking',accepted_recipe=p['id'])
            result=Result(True,{'accepted_recipe':p,'message':'Recipe accepted. Confirm actual usage and batches after cooking.'})
        elif cmd in ('/confirm','/reject') and len(parts)==2:
            if state.get('pending_preview')!=parts[1]:
                with self.store.transaction() as c:
                    prior=c.execute('SELECT 1 FROM operations WHERE request_id=%s',('user-confirm:'+parts[1],)).fetchone()
                if cmd=='/confirm' and prior:
                    return self.service.confirm_preview(parts[1],request_id='user-confirm:'+parts[1])
                return Result(False,{},'Confirmation must match the displayed pending preview')
            if cmd=='/confirm':
                result=self.service.confirm_preview(parts[1],request_id='user-confirm:'+parts[1])
                if result.ok:
                    next_stage='ready' if state.get('pending_preview_kind')=='preparation' else state.get('preview_return_stage','ready')
                    state.update(stage=next_stage,pending_preview=None,preview_return_stage=None,pending_preview_kind=None)
            else:
                result=self.service.reject_preview(parts[1])
                if result.ok:state.update(pending_preview=None,stage=state.get('preview_return_stage','ready'),preview_return_stage=None,pending_preview_kind=None)
        elif cmd=='/new-plan':
            state.pop('pending_batch_comparison',None)
            if state.get('pending_preview'):self.service.reject_preview(state['pending_preview'])
            state.update(pending_preview=None,preview_return_stage=None,pending_preview_kind=None,stage='inventory_confirmation',inventory_confirmed=False,selected_recipe=None,proposal=None,
                         accepted_recipe=None,attempts=0,clarifications=0,waiting_question=None)
            result=Result(True,{'inventory':self.service.list_inventory().data,'message':'Review inventory, then enter /inventory-ok.'})
        elif cmd=='/preview' and len(parts)==1:
            pending=state.get('pending_preview')
            with self.store.transaction() as c:
                row=c.execute('SELECT * FROM previews WHERE id=%s',(pending,)).fetchone() if pending else None
            if not row:return Result(False,{},'No pending preview')
            return Result(True,{'id':row['id'],'kind':row['kind'],'state_version':row['state_version'],
                                'status':row['status'],'changes':row['data']['changes'],'summary':row['data']['summary']})
        elif cmd=='/batches':return self.service.batch_summary()
        elif cmd=='/inventory':return self.service.list_inventory()
        elif cmd=='/daily' and len(parts)<=2:return self.service.daily_summary(parts[1] if len(parts)==2 else 'today')
        else:return Result(False,{},'Unknown command or wrong arguments; use /help')
        self.save(state)
        return result

    def propose(self,items,boxes):
        state=self.load()
        if not state['selected_recipe']:return Result(False,{},'Choose a dish before customization')
        if state['attempts']>=3:
            state['stage']='customization_limit';self.save(state)
            return Result(False,{},'Customization limit reached; select a dish again or accept current proposal explicitly')
        state['attempts']+=1
        try:
            profile=self.service.get_profile().data
            if 'meal_targets' not in profile:raise ValueError('Set separate meal and daily targets before customization')
            catalog=self.service.effective_catalog()
            catalog.validate_proposal(state['selected_recipe'],items)
            calc=catalog.calculate(state['selected_recipe'],items,boxes,Nutrients.from_dict(profile['meal_targets']))
            state['proposal']=encode({'id':str(uuid4()),'calculation':calc,'items':items,'boxes':boxes})
            state['stage']='recipe_confirmation' if state['attempts']<3 else 'customization_limit'
            result=Result(True,state['proposal'])
        except (ValueError,KeyError) as exc:
            state['stage']='customization' if state['attempts']<3 else 'customization_limit'
            result=Result(False,{},str(exc))
        self.save(state)
        return result
