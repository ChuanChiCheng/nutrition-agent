import pytest
from nutrition_demo.intent import declares_consumption


@pytest.mark.parametrize('message', [
    '我吃了一盒午餐，但不要記錄',
    '我吃了一盒午餐，但不需要登記',
    '我吃了一盒午餐，但先不記',
    "I ate a box for lunch, but don't record it",
    "I ate lunch, but I don't want to record it",
    "I did not eat lunch; please log it",
    'No need to record that I ate a box',
])
def test_meal_write_requires_positive_recording_intent(message):
    assert not declares_consumption(message)


@pytest.mark.parametrize('message', [
    '我今天午餐實際吃了一盒',
    'I ate one box for lunch',
])
def test_clear_consumption_statement_is_accepted(message):
    assert declares_consumption(message)
