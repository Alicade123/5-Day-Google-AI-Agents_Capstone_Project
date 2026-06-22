from backend.memory.interfaces import ShortTermMemory


class InMemoryShortTermMemory(ShortTermMemory):
    def __init__(self) -> None:
        self._sessions: dict[str, list[dict]] = {}

    def add_observation(self, session_id: str, observation: dict) -> None:
        self._sessions.setdefault(session_id, []).append(observation)

    def get_context(self, session_id: str) -> list[dict]:
        return list(self._sessions.get(session_id, []))

    def clear(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
