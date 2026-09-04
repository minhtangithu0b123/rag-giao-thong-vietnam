import re
import unicodedata


SMALL_TALK_RESPONSES = {
    "greeting": "Chào bạn. Bạn cần tra cứu lỗi giao thông nào thì hỏi mình nha.",
    "thanks": "Không có gì nha. Bạn cần tra cứu thêm lỗi giao thông nào thì hỏi mình tiếp.",
    "goodbye": "Tạm biệt bạn. Khi nào cần tra cứu luật giao thông thì quay lại hỏi mình nha.",
}

GREETING_PATTERNS = (
    "chao",
    "hello",
    "hi",
    "xin chao",
    "alo",
)

THANKS_PATTERNS = (
    "cam on",
    "thank",
    "thanks",
    "tks",
    "ok cam on",
    "oke cam on",
)

GOODBYE_PATTERNS = (
    "tam biet",
    "bye",
    "goodbye",
    "ngu day",
    "di day",
)

LEGAL_HINTS = (
    "phat",
    "muc phat",
    "bao nhieu",
    "luat",
    "nghi dinh",
    "dieu",
    "khoan",
    "nong do con",
    "vuot den",
    "den do",
    "qua toc do",
    "sai lan",
    "bien bao",
    "mu bao hiem",
    "giay phep lai xe",
    "bang lai",
    "o to",
    "xe may",
    "xe dap",
    "nguoi di bo",
    "may keo",
)


def normalize_text(text: str) -> str:
    text = str(text or "").lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = text.replace("đ", "d")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def exact_or_short_match(normalized_question: str, patterns: tuple[str, ...]) -> bool:
    if normalized_question in patterns:
        return True

    word_count = len(normalized_question.split())
    return word_count <= 5 and any(pattern in normalized_question for pattern in patterns)


def detect_small_talk(question: str) -> tuple[str | None, str | None]:
    normalized_question = normalize_text(question)
    if not normalized_question:
        return "small_talk", "Bạn nhập câu hỏi về luật giao thông để mình tra cứu nha."

    has_legal_hint = any(hint in normalized_question for hint in LEGAL_HINTS)
    if has_legal_hint:
        return None, None

    if exact_or_short_match(normalized_question, THANKS_PATTERNS):
        return "thanks", SMALL_TALK_RESPONSES["thanks"]

    if exact_or_short_match(normalized_question, GREETING_PATTERNS):
        return "greeting", SMALL_TALK_RESPONSES["greeting"]

    if exact_or_short_match(normalized_question, GOODBYE_PATTERNS):
        return "goodbye", SMALL_TALK_RESPONSES["goodbye"]

    if len(normalized_question.split()) <= 3:
        return "small_talk", "Mình chuyên tra cứu luật giao thông. Bạn hỏi cụ thể lỗi hoặc tình huống giao thông nha."

    return None, None
