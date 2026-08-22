from collections import defaultdict


MAX_HISTORY_MESSAGES = 8


class ChatMemory:
    def __init__(self):
        self._sessions = defaultdict(list)

    def get(self, session_id: str) -> list[dict]:
        return list(self._sessions[session_id])

    def add_turn(self, session_id: str, question: str, answer: str) -> None:
        messages = self._sessions[session_id]
        messages.append({"role": "user", "content": question})
        messages.append({"role": "assistant", "content": answer})
        self._sessions[session_id] = messages[-MAX_HISTORY_MESSAGES:]

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
