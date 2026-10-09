"""Per-visitor chat sessions.

Every visitor gets a random, unguessable session id from the server. Chat
history lives here under that id and is only ever read back for the session
that wrote it, so one visitor can never see or continue another's chat.
History is kept in memory only: it is gone when the visitor's session expires
or the service restarts.
"""
import secrets
import threading
import time

from . import config


class UnknownSession(Exception):
    pass


class SessionStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # session id -> {"seen": timestamp, "conversations": {conversation id -> turns}}
        self._sessions: dict[str, dict] = {}

    def _expire(self, now: float) -> None:
        cutoff = now - config.SESSION_TTL_SECONDS
        for session_id in [s for s, data in self._sessions.items() if data["seen"] < cutoff]:
            del self._sessions[session_id]
        # Under a flood of new sessions, drop the longest-idle ones first.
        while len(self._sessions) >= config.MAX_SESSIONS:
            del self._sessions[min(self._sessions, key=lambda s: self._sessions[s]["seen"])]

    def create(self) -> str:
        session_id = secrets.token_urlsafe(32)
        with self._lock:
            now = time.monotonic()
            self._expire(now)
            self._sessions[session_id] = {"seen": now, "conversations": {}}
        return session_id

    def _touch(self, session_id: str) -> dict:
        now = time.monotonic()
        session = self._sessions.get(session_id)
        if session is None or session["seen"] < now - config.SESSION_TTL_SECONDS:
            self._sessions.pop(session_id, None)
            raise UnknownSession(session_id)
        session["seen"] = now
        return session

    def history(self, session_id: str, conversation_id: str) -> list[dict]:
        """The earlier turns of one conversation, for the session that owns it."""
        with self._lock:
            return list(self._touch(session_id)["conversations"].get(conversation_id, []))

    def append(self, session_id: str, conversation_id: str, question: str, answer: str) -> None:
        with self._lock:
            conversations = self._touch(session_id)["conversations"]
            if conversation_id not in conversations and len(conversations) >= config.MAX_CONVERSATIONS:
                del conversations[next(iter(conversations))]
            turns = conversations.setdefault(conversation_id, [])
            turns += [
                {"role": "user", "content": question},
                {"role": "assistant", "content": answer},
            ]
            del turns[: -config.MAX_HISTORY_TURNS]


sessions = SessionStore()
