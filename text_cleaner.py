import re

def fix_mojibake(text: str) -> str:
    if not isinstance(text, str):
        return ""
    try:
        fixed = text.encode("latin1").decode("utf-8")
    except UnicodeError:
        fixed = text
    return fixed

def normalize_spaces(text: str)-> str:
    text = re.sub(r"[ \t]+" , "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
def clean_text(text: str) -> str:
    text = fix_mojibake(text)
    text = normalize_spaces(text)
    return text


def clean_value(value):
    if isinstance(value, str):
        return clean_text(value)
    return value