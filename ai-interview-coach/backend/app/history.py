"""
Lightweight persistent history of completed interviews, stored as a single
JSON file on disk (backend/data/history.json). No database needed for a
project at this scale - just append-on-finish, read-on-list.

Every record is tagged with the client_id of whoever ran that interview
(an anonymous ID generated in the browser and stored in localStorage -
see frontend/src/utils/clientId.js). list_summaries() and get_full_record()
both require a client_id and only ever return records that belong to it,
so one person can no longer see or open another person's interview
history - previously this endpoint returned everyone's data to everyone.

NOTE: this is intentionally simple (not thread-safe against true concurrent
writers, no pagination). Fine for a small deployment; swap for a real DB
(SQLite is the obvious next step) if this ever needs to handle heavier
concurrent traffic. The client_id approach is NOT real authentication -
it's a privacy-by-default anonymous identifier, not a security boundary;
anyone who copies another person's client_id (e.g. by inspecting their
browser storage) could still read their history. If real accounts/auth
are ever added, replace client_id with the authenticated user's ID.
"""
import json
import os
import threading
from datetime import datetime, timezone
from typing import Optional
from app.config import HISTORY_FILE

_lock = threading.Lock()


def _ensure_dir():
    os.makedirs(os.path.dirname(HISTORY_FILE) or ".", exist_ok=True)


def _read_all() -> list:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_completed_interview(state: dict) -> None:
    """Appends a full record of a finished interview to history.json, tagged
    with the client_id of whoever ran it (may be None for older/legacy
    sessions started before this field existed - those simply won't show
    up in anyone's filtered history list, which is the safe default)."""
    record = {
        "session_id": state.get("session_id"),
        "client_id": state.get("client_id"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "resume_summary": state.get("resume_summary", ""),
        "jd_summary": state.get("jd_summary", ""),
        "qa_log": state.get("qa_log", []),
        "final_report": state.get("final_report"),
    }
    with _lock:
        _ensure_dir()
        records = _read_all()
        records.append(record)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)


def list_summaries(client_id: str) -> list:
    """Returns lightweight summaries (no full qa_log) for the history list
    view, newest first - ONLY for records belonging to this client_id."""
    records = [r for r in _read_all() if r.get("client_id") == client_id]
    summaries = [
        {
            "session_id": r["session_id"],
            "completed_at": r["completed_at"],
            "resume_summary": r.get("resume_summary", ""),
            "jd_summary": r.get("jd_summary", ""),
            "overall_score": (r.get("final_report") or {}).get("overall_score"),
        }
        for r in records
    ]
    return list(reversed(summaries))


def get_full_record(session_id: str, client_id: str) -> Optional[dict]:
    """Only returns the record if it exists AND belongs to this client_id -
    previously any session_id would return its full transcript to anyone."""
    for r in _read_all():
        if r.get("session_id") == session_id and r.get("client_id") == client_id:
            return r
    return None