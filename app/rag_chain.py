import os

from openai import OpenAI


DEFAULT_MODEL = "gpt-4o-mini"


class RAGAnswerer:
    def __init__(self, model: str | None = None):
        self.model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
        self.client = OpenAI()

    def build_context(self, citations: list[dict]) -> str:
        context_blocks = []

        for index, citation in enumerate(citations, start=1):
            context_blocks.append(
                "\n".join(
                    [
                        f"[SOURCE {index}]",
                        f"Citation: {citation.get('citation', '')}",
                        f"Số hiệu: {citation.get('so_hieu', '')}",
                        f"Văn bản: {citation.get('ten_van_ban', '')}",
                        f"Vị trí: {citation.get('chuong', '')}, {citation.get('dieu', '')}, {citation.get('khoan', '')}",
                        f"Nhóm phương tiện: {citation.get('vehicle_group', '')}",
                        f"Nội dung: {citation.get('text', '')}",
                    ]
                )
            )

        return "\n\n".join(context_blocks)

    def build_history(self, history: list[dict] | None) -> str:
        if not history:
            return "Không có lịch sử hội thoại."

        lines = []
        for item in history[-6:]:
            role = "Người dùng" if item.get("role") == "user" else "Trợ lý"
            lines.append(f"{role}: {item.get('content', '')}")
        return "\n".join(lines)

    def fallback_answer(self, citations: list[dict]) -> str:
        if not citations:
            return "Chưa tìm thấy căn cứ đủ rõ trong dữ liệu hiện có."

        first = citations[0]
        return (
            "Mình tìm thấy căn cứ liên quan trong dữ liệu luật. "
            f"Nguồn liên quan nhất là {first.get('so_hieu', '')}, "
            f"{first.get('dieu', '')}, {first.get('khoan', '')}. "
            "Bạn xem phần trích dẫn để kiểm tra nội dung cụ thể."
        )

    def answer(self, question: str, citations: list[dict], history: list[dict] | None = None) -> str:
        if not citations:
            return "Chưa tìm thấy căn cứ đủ rõ trong dữ liệu hiện có."

        context = self.build_context(citations)
        conversation_history = self.build_history(history)

        developer_prompt = """
Bạn là trợ lý tra cứu pháp luật giao thông Việt Nam cho một hệ thống RAG.

Quy tắc bắt buộc:
- Chỉ trả lời dựa trên CONTEXT được cung cấp.
- Không tự suy đoán mức phạt, điều kiện, thời hạn, điều/khoản nếu CONTEXT không nêu rõ.
- Không tạo citation mới. Chỉ dùng số hiệu văn bản, điều, khoản có trong CONTEXT.
- Nếu CONTEXT không đủ căn cứ, trả lời: "Chưa tìm thấy căn cứ đủ rõ trong dữ liệu hiện có."
- Nếu câu hỏi thiếu thông tin quan trọng, hãy nói rõ thông tin nào đang thiếu và gợi ý người dùng hỏi cụ thể hơn.
- Với câu hỏi nồng độ cồn, nếu người dùng không nêu ngưỡng nồng độ cụ thể, không trả lời một mức phạt duy nhất. Hãy nói mức phạt phụ thuộc ngưỡng nồng độ và liệt kê các ngưỡng có trong CONTEXT.
- Với câu hỏi mức phạt theo phương tiện, hãy nêu rõ loại phương tiện nếu CONTEXT cho biết.
- Có thể dùng HISTORY để hiểu câu hỏi tiếp nối, nhưng căn cứ pháp lý vẫn phải lấy từ CONTEXT.
- Trả lời bằng tiếng Việt có dấu, ngắn gọn, dễ hiểu.
- Định dạng ưu tiên: câu tóm tắt ngắn, sau đó bullet nếu có nhiều mức.
"""

        user_prompt = f"""
QUESTION:
{question}

HISTORY:
{conversation_history}

CONTEXT:
{context}

Hãy trả lời câu hỏi dựa trên CONTEXT.
"""

        try:
            response = self.client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "developer",
                        "content": developer_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
            )
            return response.output_text.strip()
        except Exception as exc:
            return self.fallback_answer(citations) + f" (LLM chưa trả lời được: {exc})"
