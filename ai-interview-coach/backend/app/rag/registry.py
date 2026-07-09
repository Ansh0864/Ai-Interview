"""
Vector stores aren't JSON-serializable, so they can't be stored inside
LangGraph state directly (which gets checkpointed). Instead we keep a
simple process-local registry keyed by session_id.

NOTE: this is in-memory and will not survive a server restart, and won't
scale across multiple worker processes. For a production version, swap
this for a persistent Chroma instance keyed by session_id on disk, or a
hosted vector DB.
"""
from typing import Dict
from langchain_community.vectorstores import Chroma

_vectorstores: Dict[str, Chroma] = {}


def register(session_id: str, vectorstore: Chroma) -> None:
    _vectorstores[session_id] = vectorstore


def get(session_id: str) -> Chroma:
    if session_id not in _vectorstores:
        raise KeyError(f"No vectorstore registered for session {session_id}")
    return _vectorstores[session_id]


def exists(session_id: str) -> bool:
    return session_id in _vectorstores
