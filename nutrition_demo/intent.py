"""Conservative application-owned gate for ordinary meal writes.

Ambiguous language stays a question. The model cannot supply this capability.
"""
import re

NONCONSUMPTION_PATTERNS=(
    r'還沒|沒有吃|沒吃|未吃|吃了嗎|吃過嗎|是否|如果|假如|假設|要是|打算|想吃|其實|更正|改成|改為|記錯',
    r'(?:不要|不必|不需要|不用|不想|別|勿|先不)(?:幫我)?(?:記(?:錄|下)?|紀錄|登記)',
    r'\b(if|would|might|plan|will|how|what|correct|actually)\b',
    r'\b(?:don\x27t|do not|never) (?:log|record)\b',
    r'\b(?:don\x27t|do not) want to (?:log|record)\b',
    r'\bnot (?:log|record)\b',
    r'\b(?:i (?:didn\x27t|did not|haven\x27t|have not|never) (?:eat|consume)|i (?:don\x27t|do not) (?:log|record)|no need to (?:log|record))\b',
)


def normalized(message):
    return ' '.join(message.strip().lower().split())


def is_question_or_hypothetical(message):
    text=normalized(message)
    return bool(re.search(r'[?？]|多少|什麼|怎麼|會不會',text)) or any(
        re.search(pattern,text) for pattern in NONCONSUMPTION_PATTERNS)


def declares_consumption(message):
    if is_question_or_hypothetical(message):return False
    text=normalized(message)
    actual=re.search(r'吃了|吃過|吃完|吃掉|已經吃|已食用|剛吃|剛剛吃|\b(i ate|i have eaten|i just ate|i finished|i had)\b',text)
    explicit_record=re.search(r'(?:記錄|幫我記|登記).*(?:一盒|午餐|晚餐|早餐|食用)|\b(?:log|record) my (?:meal|lunch|dinner|breakfast)\b',text)
    if re.search(r'做完|烹調|煮了|做了',text) and not actual:return False
    return bool(actual or explicit_record)
