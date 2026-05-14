from src.backend.core.db import get_session_messages, list_sessions, save_message, save_session


def ensure_session(session_id: str, user_id: str) -> None:
    save_session(session_id, user_id)


def append_user_message(session_id: str, content: str) -> None:
    save_message(session_id, 'user', content, None)


def append_assistant_message(session_id: str, content: str, citations: list[dict]) -> None:
    save_message(session_id, 'assistant', content, citations)


def get_history(session_id: str, page: int, page_size: int) -> list[dict]:
    return get_session_messages(session_id, page, page_size)


def get_sessions(user_id: str) -> list[dict]:
    return list_sessions(user_id)
