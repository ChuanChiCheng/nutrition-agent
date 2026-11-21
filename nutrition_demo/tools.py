"""Versioned tool contract. Confirmation is deliberately absent from this registry."""
from copy import deepcopy

TOOL_VERSION='v1.2'
S={'type':'string'}
NULLSTR={'type':['string','null']}
Q={'type':['string','number']}

def obj(properties,required=None):
    return {'type':'object','properties':properties,'required':list(properties) if required is None else required,'additionalProperties':False}

def array(item):return {'type':'array','items':item}

ITEM=obj({'ingredient_id':S,'quantity':Q,'unit':S,'state':S})
ITEMS=array(ITEM)
ALLOC=obj({'cooking_ingredient_id':S,'quantity':Q,'unit':S})
OUTPUT=obj({'name':S,'boxes':{'type':'integer','minimum':1},'allocations':array(ALLOC)})
DISPOSITION=obj({'cooking_ingredient_id':S,'quantity':Q,'unit':S,'kind':{'enum':['remaining','loss']}})
ADDONS={'anyOf':[ITEMS,{'type':'null'}]}
NUTRIENTS=obj({k:Q for k in ('kcal','protein_g','carbs_g','fat_g')})
PROFILE=obj({'timezone':S,'meal_targets':NUTRIENTS,'daily_targets':NUTRIENTS,
             'equipment':array(S),'container_ml':Q})
SCHEMAS={
 'get_profile':obj({}),
 'preview_product_label':obj({'ingredient_id':S,'values':obj({'reference_quantity':Q,'nutrients':NUTRIENTS,'source_note':S,'source_url':NULLSTR,'price':{'anyOf':[obj({'usd':Q,'quantity':Q}),{'type':'null'}]}})}),
 'preview_profile':obj({'values':PROFILE}),
 'list_inventory':obj({}),
 'start_planning':obj({}),
 'recommend_recipes':obj({}),
 'get_recipe':obj({'recipe_id':S}),
 'select_recipe':obj({'recipe_id':S}),
 'propose_recipe':obj({'items':ITEMS,'boxes':{'type':'integer','minimum':1}}),
 'suggest_additions':obj({'batch_id':S}),
 'preview_inventory_change':obj({'items':ITEMS,'mode':{'enum':['purchase','reconcile']}}),
 'preview_preparation':obj({'recipe_id':S,'actual_usage':ITEMS,'outputs':array(OUTPUT),'prepared_on':S,
                            'confirmed_dispositions':array(DISPOSITION)},['recipe_id','actual_usage','outputs','prepared_on']),
 'preview_batch_addons':obj({'batch_id':S,'items':ITEMS}),
 'find_batches':obj({'query':S}),
 'batch_summary':obj({'batch_id':S},[]),
 'check_meal_targets':obj({'batch_id':S,'nutrients':NUTRIENTS},[]),
 'log_meal':obj({'batch_id':S,'eaten_on':S,'meal':NULLSTR,'addon_override':ADDONS}),
 'preview_reconciled_meal':obj({'items':ITEMS,'meal_input':obj({'batch_id':S,'eaten_on':S,'meal':NULLSTR,'addon_override':ADDONS}),
                               'mode':{'enum':['purchase','reconcile']}}),
 'find_events':obj({'query':obj({'date':S,'batch_id':S,'meal':NULLSTR,'event_id':S},[])}),
 'preview_correction':obj({'event_id':S,'changes':obj({'date':S,'meal':NULLSTR,'batch_id':S,'addon_override':ADDONS},[])}),
 'daily_summary':obj({'day':S}),
 'ask_user':obj({'topic':{'enum':['profile','inventory','recipe','batch','event','addons','quantity','date','product_label','details']}}),
 'explain_cooking':obj({'recipe_id':S,'evidence_ids':{'type':'array','items':S,'minItems':1,'maxItems':4}}),
}
DESCRIPTIONS={
 'log_meal':'Only a clear explicit user statement of actual consumption. Resolve batch ambiguity with find_batches first. Application supplies request_id.',
 'preview_preparation':'Preview actual cooking totals and all output allocations after recipe acceptance. Never changes inventory before application confirmation.',
 'preview_correction':'Preview correction to exactly identified event, preserving historical snapshots. Requires application confirmation.',
 'propose_recipe':'Only after user chooses a dish. Adjust quantities and at most a small permitted substitution, then authoritative exact calculation. Maximum 3 attempts.',
 'ask_user':'Ask one application-owned clarification by topic; no free-form execution or approval claims.',
 'batch_summary':'All prepared batches, or only batch_id when given: nutrients, remaining boxes, addons, and an exact per-box meal-target check.',
 'check_meal_targets':'Exactly check one box of batch_id, or hypothetical/user-given nutrients (give exactly one), against the saved meal targets. Records nothing.',
 'explain_cooking':'Answer a specific cooking question with exact verified source evidence IDs returned by get_recipe. Select at most four relevant excerpts.',
}


def tools():
    # Non-strict schemas allow optional correction fields. Local validation remains mandatory.
    return [{'type':'function','name':name,'description':DESCRIPTIONS.get(name,name.replace('_',' ')),
             'parameters':deepcopy(schema),'strict':False} for name,schema in SCHEMAS.items()]


QUESTIONS={'profile': 'Provide separate meal and daily nutrient targets, timezone, equipment, and container capacity.', 'inventory': 'Confirm inventory quantities and identify purchases or corrections.', 'recipe': 'Which recipe would you like?', 'batch': 'Which batch did you eat?', 'event': 'Which meal record should be corrected?', 'addons': 'What addons and quantities did you actually eat, or were there none?', 'quantity': 'Provide the actual quantity, unit, and raw or cooked state.', 'date': 'What was the actual consumption date?', 'product_label': 'Provide the product nutrition label, reference quantity, and unit; unknown prices may remain unknown.', 'details': 'Provide the missing details before continuing.'}
