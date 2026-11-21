"""Bind a narrow read-only meal-history question to its actual search scope."""
from dataclasses import dataclass
from datetime import date, timedelta
import re


MEAL_LOOKUP_VERSION='meal-history-lookup-v1'
MEAL_LOOKUP_INSTRUCTIONS='''This is a read-only saved-meal lookup. Use find_events with exactly the date and optional meal shown in meal_lookup context.
A successful matching search supplies the answer, including no_match. Absence means the requested dish and nutrition are unknown from saved records, not zero calories.
Do not replace this meal lookup with daily totals, invent a dish, ask which record to correct, or perform writes.'''
MONTHS={name:index for index,name in enumerate(
    ('jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'),1)}
MONTH_PATTERN=r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?'
MONTH_DATE_PATTERN=r'\b('+MONTH_PATTERN+r')\s+(\d{1,2})(?:st|nd|rd|th)?\b(?:,?\s+(\d{4})\b)?'
ISO_DATE_PATTERN=r'\b\d{4}-\d{2}-\d{2}\b'
MEAL_SUBJECT=r'(?:(?:my|the|a)\s+)?(?:(?:recorded|saved|homemade|prepared)\s+)*(?:meals?|lunch|dinner|breakfast|snack|dish)'
HISTORY_QUESTION=(
    r'(?:how (?:many|much) (?:calories|protein|carbohydrates|fat) (?:was|were) in '+MEAL_SUBJECT+
    r'|(?:what|which)(?: (?:dish|meal))? did i (?:eat|have|consume)(?: for '+MEAL_SUBJECT+r')?'
    r'|(?:show|find|list|look up|tell me about)(?: me)? '+MEAL_SUBJECT+r')'
    r' (?:on )?DAY(?:,? and how many calories did it contain)?'
)


@dataclass(frozen=True)
class MealHistoryLookup:
    day: str
    meal: str | None

    @property
    def query(self):
        return {'date':self.day,**({'meal':self.meal} if self.meal else {})}

    @classmethod
    def from_message(cls,message,local_date):
        text=message.casefold()
        # Match a complete supported read-only question, not merely keywords.
        # Unconsumed qualifiers or extra actions stay on the existing workflow.
        meals=set(re.findall(r'\b(lunch|dinner|breakfast|snack)\b',text))
        if len(meals)>1:return None
        try:
            today=date.fromisoformat(local_date)
            days={date.fromisoformat(value).isoformat() for value in re.findall(ISO_DATE_PATTERN,text)}
            for match in re.finditer(MONTH_DATE_PATTERN,text):
                month,day,year=match.groups()
                days.add(date(int(year or today.year),MONTHS[month[:3]],int(day)).isoformat())
            if re.search(r'\btoday\b',text):days.add(today.isoformat())
            if re.search(r'\byesterday\b',text):days.add((today-timedelta(days=1)).isoformat())
        except ValueError:return None
        if len(days)!=1:return None
        canonical=re.sub(ISO_DATE_PATTERN,'DAY',text)
        canonical=re.sub(MONTH_DATE_PATTERN,'DAY',canonical)
        canonical=re.sub(r'\b(today|yesterday)\b','DAY',canonical)
        canonical=' '.join(canonical.split()).rstrip(' .?!')
        if not re.fullmatch(HISTORY_QUESTION,canonical):return None
        return cls(days.pop(),next(iter(meals),None))

    def accepts(self,data):
        candidates=data.get('candidates')
        if not isinstance(candidates,list):return False
        expected='no_match' if not candidates else 'unique' if len(candidates)==1 else 'multiple'
        return (data.get('entity')=='meal_event' and data.get('query')==self.query
                and data.get('record_scope')=='recorded_prepared_meals_only'
                and data.get('match_status')==expected)
