import os
import re
import unicodedata

from openai import OpenAI


DEFAULT_REWRITE_MODEL = os.getenv("REWRITE_MODEL") or os.getenv("LLM_MODEL", "gpt-4o-mini")
FOLLOW_UP_MARKERS = (
    "vay",
    "vậy",
    "con",
    "còn",
    "thi sao",
    "thì sao",
    "muc do",
    "mức đó",
    "truong hop do",
    "trường hợp đó",
    "o to",
    "ô tô",
    "xe may",
    "xe máy",
)


class QueryRewriter:
    def __init__(self, model: str | None = None, enabled: bool | None = None):
        self.model = model or DEFAULT_REWRITE_MODEL
        self.enabled = enabled if enabled is not None else os.getenv("ENABLE_QUERY_REWRITE", "1") != "0"
        self.client = OpenAI() if self.enabled else None

    def normalize(self, text: str) -> str:
        text = str(text or "").lower()
        text = unicodedata.normalize("NFD", text)
        text = "".join(char for char in text if unicodedata.category(char) != "Mn")
        text = text.replace("đ", "d")
        return text

    def previous_user_questions(self, history: list[dict]) -> list[str]:
        return [item.get("content", "") for item in history if item.get("role") == "user" and item.get("content")]

    def should_rewrite(self, question: str, history: list[dict]) -> bool:
        if not history:
            return False

        normalized = self.normalize(question)
        word_count = len(re.findall(r"\w+", normalized))
        has_marker = any(self.normalize(marker) in normalized for marker in FOLLOW_UP_MARKERS)
        return word_count <= 10 or has_marker

    def rule_based_rewrite(self, question: str, history: list[dict]) -> str:
        previous_questions = self.previous_user_questions(history)
        if not previous_questions:
            return question

        previous = previous_questions[-1]
        normalized = self.normalize(question)

        replacements = {
            "car": ("ô tô", "oto", "xe hơi", "xe con"),
            "motorbike": ("xe máy", "mô tô", "xe gắn máy"),
            "pedestrian": ("người đi bộ", "đi bộ"),
        }
        target_phrase = None
        for phrases in replacements.values():
            for phrase in phrases:
                if self.normalize(phrase) in normalized:
                    target_phrase = phrase
                    break
            if target_phrase:
                break

        if target_phrase:
            rewritten = previous
            for phrases in replacements.values():
                for phrase in phrases:
                    rewritten = re.sub(re.escape(phrase), target_phrase, rewritten, flags=re.IGNORECASE)
            if rewritten != previous:
                return rewritten

        return f"{previous}. Câu hỏi tiếp theo: {question}"

    def llm_rewrite(self, question: str, history: list[dict], fallback: str) -> str:
        if not self.client:
            return fallback

        history_text = "\n".join(
            f"{item.get('role', '')}: {item.get('content', '')}" for item in history[-6:]
        )

        prompt = f"""
Bạn viết lại câu hỏi tiếp nối thành một câu hỏi độc lập để dùng cho bước retrieval trong hệ thống RAG luật giao thông Việt Nam.

Yêu cầu:
- Chỉ viết lại câu hỏi, không trả lời câu hỏi.
- Giữ đúng ý người dùng.
- Nếu câu hỏi đã độc lập, trả lại nguyên câu hỏi.
- Không thêm mức phạt, điều, khoản, căn cứ pháp lý nếu người dùng chưa nêu.
- Nếu câu hỏi mới chỉ đổi loại phương tiện, hãy thay loại phương tiện vào chủ đề ở câu trước.
- Output chỉ là một dòng câu hỏi tiếng Việt.

HISTORY:
{history_text}

CURRENT QUESTION:
{question}
"""

        try:
            response = self.client.responses.create(
                model=self.model,
                instructions="Bạn là bộ viết lại truy vấn cho RAG. Chỉ xuất câu hỏi đã viết lại, không giải thích.",
                input=prompt,
                max_output_tokens=120,
            )
            rewritten = response.output_text.strip().strip('"')
            if not rewritten:
                return fallback
            return rewritten.splitlines()[0].strip()
        except Exception:
            return fallback

    def rewrite(self, question: str, history: list[dict]) -> tuple[str, bool]:
        if not self.should_rewrite(question, history):
            return question, False

        fallback = self.rule_based_rewrite(question, history)
        rewritten = self.llm_rewrite(question, history, fallback)
        return rewritten, rewritten != question
