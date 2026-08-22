import re


MOJIBAKE_MARKERS = ("Ä", "áº", "á»", "Æ", "Ã", "Â")


def looks_mojibake(text: str) -> bool:
    return any(marker in text for marker in MOJIBAKE_MARKERS)


def fix_mojibake(text: str) -> str:
    if not isinstance(text, str):
        return ""

    if not looks_mojibake(text):
        return text

    for source_encoding in ("cp1252", "latin1"):
        try:
            return text.encode(source_encoding).decode("utf-8")
        except UnicodeError:
            continue

    return text


def normalize_spaces(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
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
