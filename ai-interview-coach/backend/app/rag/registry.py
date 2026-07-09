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
