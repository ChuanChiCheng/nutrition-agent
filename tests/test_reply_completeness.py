"""Replies must state the facts a user asked for, computed by the application, not by model prose."""
from decimal import Decimal as D

from nutrition_demo.display import render
from nutrition_demo.models import Nutrients, Result
from nutrition_demo.nutrition import validate_targets

from test_demo_agent import Responses, agent, profile


YOGURT = {'ingredient_id': 'yogurt', 'quantity': '1', 'unit': 'serving', 'state': 'packaged'}


def test_addon_confirmation_lists_saved_items_and_is_not_rendered_as_inventory():
    text = render(Result(True, {'batch_id': 'batch-1', 'addon_version': 2,
                                'items': [{**YOGURT, 'name': 'Synthetic yogurt'}]}))
    assert 'Default addon plan saved for batch batch-1' in text
    assert 'Synthetic yogurt: 1 serving' in text
    assert 'no intake was recorded and no stock was consumed' in text
    assert 'Ingredient inventory' not in text


def test_meal_confirmation_states_batch_date_meal_and_remaining_boxes():
    text = render(Result(True, {'event_id': 'e1', 'batch_id': 'batch-1', 'batch_name': 'Curry lunch',
                                'eaten_on': '2026-11-18', 'meal': 'lunch', 'remaining_boxes': 3,
                                'total_nutrients': {'kcal': 600, 'protein_g': 40, 'carbs_g': 65, 'fat_g': 20}}))
    assert 'Meal recorded: Curry lunch (batch-1) | Date 2026-11-18 | Meal lunch' in text
    assert 'remaining boxes in this batch: 3' in text
    assert '600 kcal' in text


def test_correction_result_keeps_its_existing_wording():
    text = render(Result(True, {'event_id': 'e1', 'event': {'eaten_on': '2026-11-17'}}))
    assert text == 'Meal record updated: e1'


def test_empty_lookup_and_empty_day_say_that_nothing_is_known():
    assert 'No matching records were found' in render(Result(True, {'candidates': [], 'needs_clarification': True}))
    zero = {'kcal': 0, 'protein_g': 0, 'carbs_g': 0, 'fat_g': 0}
    text = render(Result(True, {'day': '2026-11-10', 'scope': 'recorded_prepared_meals_only', 'events': 0,
                                'box': zero, 'addons': zero, 'total': zero, 'daily_targets': None, 'progress': None}))
    assert 'No prepared meals are recorded for this day' in text
    assert 'cannot be determined' in text and 'kcal' not in text


def test_batch_summary_render_shows_exact_meal_target_check():
    check = validate_targets(Nutrients(600, 40, 65, 20), Nutrients(600, 40, 65, 20))
    batch = {'id': 'batch-1', 'name': 'Curry lunch', 'remaining_boxes': 4, 'total_boxes': 6,
             'box_nutrients': {'kcal': 600, 'protein_g': 40, 'carbs_g': 65, 'fat_g': 20},
             'meal_nutrients': {'kcal': 600, 'protein_g': 40, 'carbs_g': 65, 'fat_g': 20},
             'box_cost': {'complete': True, 'total': 0, 'known_subtotal': 0}, 'default_addons': [],
             'sources': [{'status': 'synthetic'}], 'meal_target_check': check}
    text = render(Result(True, {'batches': [batch]}))
    assert 'One box vs meal targets: all four nutrients pass' in text
    assert 'Calories: actual 600 kcal; target 600 kcal; allowed 570–630 kcal; difference 0; Pass' in text
    assert 'Data source status: synthetic' in text


def test_hypothetical_check_reports_overall_failure_when_one_nutrient_fails():
    check = validate_targets(Nutrients(D('569.9'), 40, 65, 20), Nutrients(600, 40, 65, 20))
    text = render(Result(True, {'hypothetical_check': check}))
    assert 'nothing is recorded' in text
    assert 'not all four nutrients pass, so the overall result fails' in text
    assert 'Calories: actual 569.9 kcal' in text and 'Fail' in text


def test_service_adds_target_check_remaining_boxes_and_saved_addons(prepared):
    s, batch = prepared
    profile(s)
    summary = s.batch_summary().data['batches'][0]
    assert summary['meal_target_check']['metrics'].keys() == {'kcal', 'protein_g', 'carbs_g', 'fat_g'}
    assert isinstance(summary['meal_target_check']['passed'], bool)

    preview = s.preview_batch_addons(batch, [YOGURT])
    saved = s.confirm_preview(preview.data['id'], 'addons')
    assert saved.ok and saved.data['items'][0]['ingredient_id'] == 'yogurt'

    meal = s.log_meal(batch, '2026-11-18', 'lunch', 'meal-1')
    assert meal.ok and meal.data['remaining_boxes'] == 7


def test_agent_is_reminded_once_to_answer_through_tools(prepared):
    from nutrition_demo.agent import TOOL_REMINDER
    s, _ = prepared
    profile(s)
    a = agent(s, [[], [('batch_summary', {})], []])
    r = a.handle('Does the batch meet the meal targets?')
    assert [t['name'] for t in r.data['tool_results']] == ['batch_summary']
    assert r.data['counts']['model_calls'] == 3
    sent = a.client.responses.inputs[-1]['input']
    assert sent.count({'role': 'user', 'content': TOOL_REMINDER}) == 1

    a.client.responses = Responses([[], []])
    r = a.handle('hello')
    assert r.data['tool_results'] == [] and r.data['counts']['model_calls'] == 2


def test_check_meal_targets_tool_uses_saved_targets_and_records_nothing(prepared):
    s, _ = prepared
    profile(s)
    a = agent(s, [[('check_meal_targets', {'nutrients': {'kcal': '189', 'protein_g': '12.5', 'carbs_g': 25, 'fat_g': '2.5'}})], []])
    r = a.handle('If a box had 189 kcal, would it pass?')
    check = r.data['tool_results'][0]['result']['data']['hypothetical_check']
    assert check['passed'] is False and check['metrics']['kcal']['passed'] is False
    assert s.store.info()['counts']['events'] == 0


def test_batch_tools_accept_a_batch_id(prepared):
    s, batch = prepared
    profile(s)
    assert [b['id'] for b in s.batch_summary(batch).data['batches']] == [batch]
    assert not s.batch_summary('missing').ok

    a = agent(s, [[('check_meal_targets', {'batch_id': batch})], []])
    r = a.handle('Does this batch meet the meal targets?')
    data = r.data['tool_results'][0]['result']['data']['batch_target_check']
    assert data['batch_id'] == batch and isinstance(data['check']['passed'], bool)
    assert 'checked against the saved meal targets' in render(r)


def test_check_meal_targets_requires_exactly_one_input(prepared):
    s, batch = prepared
    profile(s)
    nutrients = {'kcal': 200, 'protein_g': '12.5', 'carbs_g': 25, 'fat_g': '2.5'}
    for args in ({}, {'batch_id': batch, 'nutrients': nutrients}):
        a = agent(s, [[('check_meal_targets', args)], []])
        result = a.handle('Check targets').data['tool_results'][0]['result']
        assert not result['ok'] and 'exactly one' in result['error']
