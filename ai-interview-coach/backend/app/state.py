from typing import TypedDict, List, Optional, Literal

Round = Literal["behavioral", "hr", "coding"]


class QAEntry(TypedDict):
    round: str
    question: str
    answer: str
    score: int  # 1-10
    feedback: str
    confidence_flags: List[str]  # e.g. ["hedging language", "very short answer"]


class InterviewState(TypedDict, total=False):
    session_id: str
    client_id: Optional[str]  # anonymous per-browser identity, used to scope /api/history so
                               # one person can't see or open another person's interview history

    # Source documents (raw text, extracted once at ingestion)
    resume_text: str
    jd_text: str
    resume_summary: str
    jd_summary: str
    key_skills: List[str]

    # Set True once ingestion has run; used by the conditional entry point
    # to decide whether an incoming call is "start a session" or "answer a turn".
    ingested: bool

    # Round management
    round_order: List[Round]
    round_index: int
    current_round: Round
    questions_asked_in_round: int
    max_questions_per_round: int

    # Turn-level working memory
    current_question: str
    is_followup: bool
    followups_used_on_current_question: int
    last_answer: str
    declared_language: Optional[str]  # e.g. "python" - only meaningful during the coding round

    # Previous-turn results shown in the UI (these were missing before,
    # which is why the "/10" score never rendered)
    last_score: Optional[int]
    last_feedback: Optional[str]
    last_confidence_flags: List[str]

    # History / results
    conversation: List[dict]  # [{"role": "interviewer"|"candidate", "content": str}]
    qa_log: List[QAEntry]

    # Control flow
    next_action: Literal["ask_followup", "next_question", "next_round", "finish"]
    finished: bool
    final_report: Optional[dict]