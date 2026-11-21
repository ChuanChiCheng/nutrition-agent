"""Persistent partial actual-preparation facts and application-owned questions."""
from copy import deepcopy
from datetime import date
import re
import jsonschema

from .models import Result, decimal, encode
from .tools import SCHEMAS, DESCRIPTIONS, obj, array, S, Q, ALLOC, DISPOSITION


PREPARATION_VERSION='preparation-clarification-v1'
PARTIAL_ITEM=obj({'ingredient_id':S,'quantity':Q,'unit':S,'state':S},['ingredient_id'])
PARTIAL_OUTPUT=obj({'name':{'type':'string','minLength':1},'boxes':{'type':'integer','minimum':1},
                    'allocations':array(ALLOC)},['name'])
DRAFT_SCHEMA=obj({'actual_usage':array(PARTIAL_ITEM),'outputs':array(PARTIAL_OUTPUT),
                  'prepared_on':S,'confirmed_dispositions':array(DISPOSITION)},[])
PREPARATION_INSTRUCTIONS='''An actual-preparation draft is active. Record supplied facts with update_preparation_draft before asking questions or previewing.
Only extract actual facts supplied by the user. Do not copy planned amounts into actual usage, assume an omitted ingredient was unused, default an absent date, or infer multi-batch allocations from box counts.
Python derives missing fields/conflicts. Use ask_user with the first issue's topic to ask its application-owned question. A complete draft needs no clarification: call preview_preparation with no arguments.
Only external /confirm can consume inventory. Drafts and previews are not completed cooking writes.'''
PREPARATION_DESCRIPTIONS={**DESCRIPTIONS,
    'update_preparation_draft':'Merge supplied partial actual ingredient fields and output fields by ingredient ID/batch name. Preserve known fields. Omission confirmation is external, never a tool argument.',
    'preview_preparation':'Preview the complete application-owned preparation draft with no arguments. Missing facts/conflicts must be resolved first.',
    'ask_user':'Ask the first specific missing-field/conflict question returned by the preparation draft, using its topic.',
}


class PreparationDraft:
    def __init__(self,state,data=None):
        self.recipe_id=state['selected_recipe']
        self.accepted_recipe=state['accepted_recipe']
        self.planned_ids=tuple(i['ingredient_id'] for i in state['proposal']['items'])
        self.data=deepcopy(data or {'actual_usage':[],'outputs':[],'omitted_ingredients':[],'capture_attempted':False})
        self.status='running'
        self.corrections=0

    @classmethod
    def from_message(cls,message,state):
        if state.get('stage')!='cooking' or not state.get('accepted_recipe') or not state.get('proposal'):return None
        saved=state.get('preparation_draft')
        valid=saved and saved.get('recipe_id')==state['selected_recipe'] and saved.get('accepted_recipe')==state['accepted_recipe']
        text=' '.join(message.casefold().split()).strip()
        if re.match(r'^(?:please )?preview (?:preparing|cooking|preparation|actual cooking)\b',text):
            if re.search(r'\b(log|record|correct|fix|edit|buy|purchase|profile|inventory|summarize|summarise)\b',text):return None
            draft=cls(state)
            for identity in draft.planned_ids:
                phrase=r'(?:no '+re.escape(identity)+r' was used|i did not use '+re.escape(identity)+r')'
                if re.search(r'(?:^|[.;]\s*)'+phrase+r'(?=$|[.;])',text):
                    draft.data['omitted_ingredients'].append(identity)
            return draft
        if valid and text.rstrip('.!?') in ('continue preparation','continue the preparation','continue cooking preview'):
            return cls(state,saved['data'])
        if valid and saved['data'].get('question'):
            draft=cls(state,saved['data'])
            question=draft.data['question']
            if question['kind']=='omission' and draft.apply_reply(message).ok:return draft
            # Replies containing actual quantities/dates may be extracted by the
            # model; a new question or unrelated command never inherits scope.
            if not re.search(r'[?]|\b(show|find|list|what|how|correct|record|log|buy|purchase|preview|recommend|profile|targets?|inventory|set|add|edit|fix|change|move|update|delete|remove|summarize|summarise)\b',text):
                if re.search(r'\d|\b(raw|cooked|dry|packaged|g|kg|ml|grams|servings?|today|yesterday|allocate|one|two|three|four|five|six|seven|eight|nine|ten)\b',text) or question['kind']=='ingredient' and re.fullmatch(r'[a-z][a-z_ -]{0,60}[.!]?',text):
                    draft.data['reply_to']=deepcopy(question)
                    draft.data.pop('question',None)
                    return draft
        return None

    def schemas(self):
        names=('get_profile','list_inventory','get_recipe','ask_user')
        return {**{name:SCHEMAS[name] for name in names},
                'update_preparation_draft':DRAFT_SCHEMA,'preview_preparation':obj({})}

    def bound_to(self,state):
        return (state.get('stage')=='cooking' and state.get('selected_recipe')==self.recipe_id
                and state.get('accepted_recipe')==self.accepted_recipe
                and (state.get('proposal') or {}).get('id')==self.accepted_recipe)

    def saved(self):
        return {'recipe_id':self.recipe_id,'accepted_recipe':self.accepted_recipe,'data':deepcopy(self.data)}

    def update(self,patch):
        try:
            jsonschema.validate(patch,DRAFT_SCHEMA)
            updated=deepcopy(self.data)
            reply=updated.get('reply_to',{})
            replacements=patch.get('actual_usage',[])
            if reply.get('kind')=='ingredient' and replacements:
                old=reply['ingredient_id']
                if len(replacements)!=1:raise ValueError('Provide one verified replacement for the pending ingredient identity')
                new=replacements[0]['ingredient_id']
                if new!=old:
                    if any(item['ingredient_id']==new for item in updated['actual_usage']):
                        raise ValueError('That ingredient already exists; start a revised preparation request rather than merging quantities')
                    for item in updated['actual_usage']:
                        if item['ingredient_id']==old:item['ingredient_id']=new
                    for output in updated['outputs']:
                        for allocation in output.get('allocations',[]):
                            if allocation['cooking_ingredient_id']==old:allocation['cooking_ingredient_id']=new
                    for entry in updated.get('confirmed_dispositions',[]):
                        if entry['cooking_ingredient_id']==old:entry['cooking_ingredient_id']=new
                updated.pop('reply_to',None)
            for key,identity in (('actual_usage','ingredient_id'),('outputs','name')):
                if key not in patch:continue
                if len({row[identity] for row in patch[key]})!=len(patch[key]):raise ValueError('Duplicate preparation entry')
                rows={row[identity]:row for row in updated[key]}
                for row in patch[key]:
                    if key=='actual_usage' and row['ingredient_id'] in updated['omitted_ingredients']:
                        raise ValueError('The user explicitly reported no '+row['ingredient_id']+'; start a revised preparation request before including it.')
                    if key=='actual_usage' and 'quantity' in row:decimal(row['quantity'],positive=True)
                    if any(field in row and not row[field].strip() for field in ('unit','state')):
                        raise ValueError('Actual unit/state cannot be blank; omit unknown fields')
                    if key=='outputs' and 'allocations' in row:
                        for allocation in row['allocations']:decimal(allocation['quantity'],positive=True)
                    rows[row[identity]]={**rows.get(row[identity],{}),**deepcopy(row)}
                updated[key]=list(rows.values())
            for key in ('prepared_on','confirmed_dispositions'):
                if key in patch:updated[key]=deepcopy(patch[key])
            for entry in updated.get('confirmed_dispositions',[]):decimal(entry['quantity'],positive=True)
            if 'prepared_on' in updated:date.fromisoformat(updated['prepared_on'])
            updated.pop('question',None)
            updated['capture_attempted']=True
            self.data=updated
            return Result(True,{'preparation_details':deepcopy(self.data)})
        except (jsonschema.ValidationError,ValueError,TypeError) as exc:
            return Result(False,{},str(exc) if isinstance(exc,ValueError) else 'Invalid partial preparation fields')

    def issues(self,catalog):
        issues=[]
        def issue(kind,topic,question,**details):
            issues.append({'kind':kind,'topic':topic,'question':question,**details})
        actual=self.data['actual_usage']
        if not actual:
            issue('ingredients','details','Which ingredients did you actually use? Provide their quantities, units, and raw/cooked states.')
            return issues
        for item in actual:
            identity=item['ingredient_id']
            try:reference=catalog.ingredient(identity)
            except ValueError:
                issue('ingredient','details',f'Which verified ingredient or product does {identity} refer to?',ingredient_id=identity)
                continue
            for field in ('quantity','unit','state'):
                if field not in item:
                    prompts={'quantity':f'How much {identity} did you actually use'+(' in '+item['unit'] if item.get('unit') else '')+'?',
                             'unit':f'What unit is the actual quantity for {identity}?',
                             'state':f'What was the actual raw/cooked state of {identity}?'}
                    issue(field,'quantity',prompts[field],ingredient_id=identity)
            if item.get('unit') and item['unit']!=reference['unit'] or item.get('state') and item['state']!=reference['state']:
                issue('basis','quantity',f'The supplied basis for {identity} differs from verified {reference["unit"]}/{reference["state"]} data. Provide verified matching usage or a product label; no conversion is assumed.',ingredient_id=identity)
        actual_ids={item['ingredient_id'] for item in actual}
        for identity in self.planned_ids:
            if identity not in actual_ids and identity not in self.data['omitted_ingredients']:
                issue('omission','details',f'The accepted recipe includes {identity}, but the actual-usage draft omits it. Did you use any {identity}? Reply No if none was used, or Yes and provide its actual quantity, unit, and state.',ingredient_id=identity)
        if not self.data.get('prepared_on'):issue('date','date','On what date did you actually prepare these batches?')
        outputs=self.data['outputs']
        if not outputs:issue('outputs','details','What output batches did you prepare, and how many boxes are in each?')
        for output in outputs:
            name=output['name']
            if 'boxes' not in output:issue('boxes','quantity',f'How many boxes are in {name}?',output=name)
            if not output.get('allocations'):
                issue('allocations','details',f'How much of each actual ingredient went into {name}? Provide ingredient quantities and units; box counts do not establish ingredient allocation.',output=name)
        if not issues:
            allocated={identity:decimal(0) for identity in actual_ids}
            for output in outputs:
                seen=set()
                for entry in output['allocations']:
                    identity=entry['cooking_ingredient_id']
                    item=next((i for i in actual if i['ingredient_id']==identity),None)
                    if identity in seen or item is None or entry['unit']!=item['unit']:
                        issue('allocations','details',f'Correct the ingredient identity, duplicate entry, or unit in allocations for {output["name"]}.',output=output['name'])
                        continue
                    seen.add(identity)
                    allocated[identity]+=decimal(entry['quantity'],positive=True)
            for entry in self.data.get('confirmed_dispositions',[]):
                identity=entry['cooking_ingredient_id']
                item=next((i for i in actual if i['ingredient_id']==identity),None)
                if item is None or entry['unit']!=item['unit']:
                    issue('conservation','details','Correct the ingredient identity or unit for the reported remaining/lost quantity.')
                else:allocated[identity]+=decimal(entry['quantity'],positive=True)
            for item in actual:
                difference=decimal(item['quantity'])-allocated[item['ingredient_id']]
                if difference:
                    issue('conservation','details',f'Allocations and reported remaining/loss leave a difference of {difference} {item["unit"]} for {item["ingredient_id"]}. Correct the allocation or specify actual remaining/lost quantities.',ingredient_id=item['ingredient_id'])
        return issues

    def ask(self,topic,catalog):
        issues=self.issues(catalog)
        if not issues:return Result(False,{},'The preparation draft is complete; preview it instead of asking again.')
        first=issues[0]
        if not self.data.get('capture_attempted'):
            return Result(False,{},'Capture the preparation facts already supplied with update_preparation_draft before asking.')
        if topic!=first['topic']:return Result(False,{},'Use ask_user topic '+first['topic']+': '+first['question'])
        self.data['question']=deepcopy(first)
        self.status='awaiting_user'
        return Result(True,{'waiting_question':first['question']})

    def apply_reply(self,message):
        question=self.data.get('question')
        if not question or question['kind']!='omission':return Result(False,{},'No ingredient omission question is pending')
        text=' '.join(message.casefold().split()).rstrip('.!')
        identity=question['ingredient_id']
        if text in ('no','none','no '+identity,'no '+identity+' was used','i did not use '+identity,
                    'i did not use any '+identity,'no, i did not use '+identity,'no, i did not use any '+identity):
            self.data['omitted_ingredients']=list(dict.fromkeys(self.data['omitted_ingredients']+[identity]))
        elif text in ('yes','yes i used it'):
            self.data['actual_usage'].append({'ingredient_id':identity})
        else:return Result(False,{},'Answer the pending ingredient question explicitly or provide its actual usage.')
        self.data.pop('question',None)
        return Result(True,{})

    def payload(self,catalog):
        issues=self.issues(catalog)
        if issues:return Result(False,{},'Cannot preview preparation yet: '+issues[0]['question'])
        return Result(True,{'recipe_id':self.recipe_id,
            **{key:deepcopy(self.data[key]) for key in ('actual_usage','outputs','prepared_on')},
            'confirmed_dispositions':deepcopy(self.data.get('confirmed_dispositions',[]))})

    def feedback(self,reason):
        if self.corrections>=2:
            self.status='incomplete'
            return None
        self.corrections+=1
        return {'preparation_action_rejected':reason,
                'next_step':'Capture supplied facts with update_preparation_draft, then ask the first derived issue or preview the complete draft.'}
