from fastapi import APIRouter, HTTPException, Header
from app import history

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
async def list_history(x_client_id: str = Header(...)):
    """Lightweight summaries of every completed interview belonging to this
    browser's client_id, newest first. x_client_id is required - without it
    there's no way to know whose history to return."""
    return history.list_summaries(x_client_id)


@router.get("/{session_id}")
async def get_history_record(session_id: str, x_client_id: str = Header(...)):
    """Full record (qa_log + final_report) for one completed interview -
    only returned if it belongs to the requesting client_id."""
    record = history.get_full_record(session_id, x_client_id)
    if record is None:
        raise HTTPException(404, "No history record found for this session.")
    return record