import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.rag.ingest import extract_text_from_upload, build_session_vectorstore
from app.rag import registry
from app.graph.build import interview_graph
from app.graph.llm import ModelUnavailableError, RateLimitExceeded
from app.config import MAX_QUESTIONS_PER_ROUND
from app.voice.stt import transcribe_audio
from app.voice.tts import synthesize_speech, TTSError, TTSNotConfigured

router = APIRouter(prefix="/api/session", tags=["session"])

class AnswerRequest(BaseModel):
    session_id: str
    answer: str
    language: Optional[str] = None  # only meaningful for coding-round code answers


class TTSRequest(BaseModel):
    text: str


def _public_view(state: dict) -> dict:
    """Strip internal fields before sending state back to the frontend."""
    return {
        "session_id": state.get("session_id"),
        "current_round": state.get("current_round"),
        "questions_asked_in_round": state.get("questions_asked_in_round"),
        "max_questions_per_round": state.get("max_questions_per_round"),
        "current_question": state.get("current_question"),
        "is_followup": state.get("is_followup"),
        "finished": state.get("finished", False),
        "last_score": state.get("last_score"),
        "last_feedback": state.get("last_feedback"),
        "last_confidence_flags": state.get("last_confidence_flags", []),
        "qa_log": state.get("qa_log", []),
        "final_report": state.get("final_report"),
    }


def _run_turn(config: dict, turn_input: dict) -> dict:
    """
    Shared invocation path for both text and voice answers. LLM calls
    already retry internally on rate limits (see app/graph/llm.py); if it
    still fails after retries, nothing has been committed to the
    checkpoint, so the caller can safely retry the exact same request.
    """
    try:
        result = interview_graph.invoke(turn_input, config=config)
        return _public_view(result)
    except ModelUnavailableError as e:
        raise HTTPException(500, str(e))
    except RateLimitExceeded as e:
        # Structured detail (not just a string) so the frontend can show
        # a real countdown instead of a vague "try again later" message.
        raise HTTPException(429, {
            "message": str(e),
            "retry_after_seconds": e.retry_after_seconds,
        })
    except Exception as e:
        raise HTTPException(500, f"Error processing turn: {str(e)}")


@router.post("/start")
async def start_session(
    resume: UploadFile = File(...),
    jd: UploadFile = File(None),
    jd_text: str = Form(None),
    client_id: str = Form(None),
):
    if jd is None and not jd_text:
        raise HTTPException(400, "Provide either a JD file or jd_text.")

    session_id = str(uuid.uuid4())
    resume_bytes = await resume.read()
    resume_text = extract_text_from_upload(resume.filename, resume_bytes)

    if jd is not None:
        jd_bytes = await jd.read()
        jd_full_text = extract_text_from_upload(jd.filename, jd_bytes)
    else:
        jd_full_text = jd_text

    if not resume_text.strip():
        raise HTTPException(400, "Could not extract any text from the resume file.")

    vectorstore = build_session_vectorstore(session_id, resume_text, jd_full_text)
    registry.register(session_id, vectorstore)

    config = {"configurable": {"thread_id": session_id}}
    return _run_turn(config, {
        "session_id": session_id,
        "client_id": client_id,
        "resume_text": resume_text,
        "jd_text": jd_full_text,
        "max_questions_per_round": MAX_QUESTIONS_PER_ROUND,
    })


@router.post("/answer")
async def submit_answer(req: AnswerRequest):
    config = {"configurable": {"thread_id": req.session_id}}
    existing = interview_graph.get_state(config)

    if not existing.values:
        raise HTTPException(404, "Session not found. Start a new session first.")
    if existing.values.get("finished"):
        raise HTTPException(400, "This interview has already finished.")

    return _run_turn(config, {"last_answer": req.answer, "declared_language": req.language})


@router.post("/{session_id}/answer-audio")
async def submit_answer_audio(session_id: str, audio: UploadFile = File(...)):
    """Voice answer: transcribe with local Whisper, then run the normal turn."""
    config = {"configurable": {"thread_id": session_id}}
    existing = interview_graph.get_state(config)

    if not existing.values:
        raise HTTPException(404, "Session not found. Start a new session first.")
    if existing.values.get("finished"):
        raise HTTPException(400, "This interview has already finished.")

    audio_bytes = await audio.read()
    try:
        transcript = transcribe_audio(audio_bytes, filename_hint=audio.filename or "audio.webm")
    except Exception as e:
        raise HTTPException(500, f"Could not transcribe audio: {str(e)}")

    if not transcript.strip():
        raise HTTPException(400, "Couldn't hear anything in that recording — try again.")

    result = _run_turn(config, {"last_answer": transcript})
    result["transcript"] = transcript
    return result


@router.post("/tts")
async def text_to_speech(req: TTSRequest):
    """Synthesizes the interviewer's voice for a given question via ElevenLabs."""
    try:
        audio_bytes = synthesize_speech(req.text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except TTSNotConfigured as e:
        raise HTTPException(503, {"reason": "not_configured", "message": str(e)})
    except TTSError as e:
       
        raise HTTPException(e.status_code, {"reason": "api_error", "message": str(e)})


@router.get("/{session_id}/state")
async def get_state(session_id: str):
    config = {"configurable": {"thread_id": session_id}}
    existing = interview_graph.get_state(config)
    if not existing.values:
        raise HTTPException(404, "Session not found.")
    return _public_view(existing.values)