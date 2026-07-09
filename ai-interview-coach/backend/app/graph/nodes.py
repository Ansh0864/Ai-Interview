import logging
from app.state import InterviewState
from app.graph.llm import call_llm_json
from app.graph.prompts import (
    COMBINED_START_PROMPT, COMBINED_TURN_PROMPT, FINAL_REPORT_PROMPT,
    NEXT_STEP_SAME_ROUND, NEXT_STEP_NEW_ROUND, NEXT_STEP_FINAL,
    LANGUAGE_CHECK_INSTRUCTIONS, ROUND_INSTRUCTIONS, ROUND_LABELS,
)
from app.rag import registry
from app.rag.ingest import retrieve_context
from app.config import MAX_QUESTIONS_PER_ROUND, MAX_FOLLOWUPS_PER_QUESTION
from app import history

logger = logging.getLogger("interview_coach.nodes")

def _round_history_text(state: InterviewState) -> str:
    current_round = state["current_round"]
    lines = []
    for entry in state.get("qa_log", []):
        if entry["round"] == current_round:
            lines.append(f"Q: {entry['question']}\nA: {entry['answer']}")
    return "\n\n".join(lines) if lines else "(no questions asked yet this round)"


def _build_final_report(state: InterviewState) -> dict:
    qa_summary = "\n\n".join(
        f"[{e['round'].upper()}] Q: {e['question']}\nA: {e['answer']}\nScore: {e['score']}/10\nFeedback: {e['feedback']}"
        for e in state.get("qa_log", [])
    )
    return call_llm_json(
        FINAL_REPORT_PROMPT.format(
            resume_summary=state.get("resume_summary", ""),
            jd_summary=state.get("jd_summary", ""),
            qa_summary=qa_summary,
        )
    )


def start_interview_node(state: InterviewState) -> dict:
    """
    Atomic + combined: summarizes resume/JD AND generates the first
    question in a SINGLE LLM call (previously two separate calls).
    """
    round_key = "behavioral"
    vectorstore = registry.get(state["session_id"])
    query = f"{round_key} interview relevant experience and background"
    retrieved = retrieve_context(vectorstore, query, k=3)

    result = call_llm_json(
        COMBINED_START_PROMPT.format(
            round_label=ROUND_LABELS[round_key],
            resume_text=state["resume_text"][:6000],
            jd_text=state["jd_text"][:4000],
            retrieved_context=retrieved,
            round_instructions=ROUND_INSTRUCTIONS[round_key],
        )
    )

    question = result.get("first_question", "Tell me about yourself and your background.")

    return {
        "resume_summary": result.get("resume_summary", ""),
        "jd_summary": result.get("jd_summary", ""),
        "key_skills": result.get("key_skills", []),
        "round_order": ["behavioral", "hr", "coding"],
        "round_index": 0,
        "current_round": round_key,
        "questions_asked_in_round": 0,
        "followups_used_on_current_question": 0,
        "is_followup": False,
        "conversation": [{"role": "interviewer", "content": question}],
        "qa_log": [],
        "finished": False,
        "last_score": None,
        "last_feedback": None,
        "last_confidence_flags": [],
        "ingested": True,
        "current_question": question,
    }


def process_turn_node(state: InterviewState) -> dict:
    """
    Atomic + combined: scores the answer AND generates whatever comes
    next (follow-up / fresh question / next round's opener) in a SINGLE
    LLM call. Only two situations still need a second call: advancing
    into a brand new round needs retrieval context specific to that round
    (cheap, no extra LLM call), and finishing the interview needs the
    separate final-report call (unavoidable - it aggregates the whole log).
    """
    round_key = state["current_round"]
    round_order = state["round_order"]
    round_index = state["round_index"]
    max_q = state.get("max_questions_per_round", MAX_QUESTIONS_PER_ROUND)

    # Deterministic bookkeeping computed BEFORE the LLM call, since it
    # doesn't depend on the model's judgment - only needs_followup does.
    tentative_questions_asked = state["questions_asked_in_round"] + (0 if state.get("is_followup") else 1)
    is_last_question_of_round = tentative_questions_asked >= max_q
    is_final_round = round_index + 1 >= len(round_order)

    if not is_last_question_of_round:
        next_step_instructions = NEXT_STEP_SAME_ROUND.format(
            question_number=tentative_questions_asked,
            max_questions=max_q,
            round_label=ROUND_LABELS[round_key],
            round_history=_round_history_text(state),
            round_instructions=ROUND_INSTRUCTIONS[round_key],
        )
        next_question_instruction = "the next fresh question in the SAME round"
    elif not is_final_round:
        next_round_key = round_order[round_index + 1]
        next_step_instructions = NEXT_STEP_NEW_ROUND.format(
            round_label=ROUND_LABELS[round_key],
            next_round_label=ROUND_LABELS[next_round_key],
            next_round_instructions=ROUND_INSTRUCTIONS[next_round_key],
        )
        next_question_instruction = f"the OPENING question of the {ROUND_LABELS[next_round_key]} round"
    else:
        next_step_instructions = NEXT_STEP_FINAL.format(round_label=ROUND_LABELS[round_key])
        next_question_instruction = "empty string, the interview is ending"

    declared_language = state.get("declared_language")
    language_check_instructions = (
        LANGUAGE_CHECK_INSTRUCTIONS.format(declared_language=declared_language)
        if declared_language else ""
    )

    result = call_llm_json(
        COMBINED_TURN_PROMPT.format(
            round_label=ROUND_LABELS[round_key],
            resume_summary=state.get("resume_summary", ""),
            jd_summary=state.get("jd_summary", ""),
            question=state["current_question"],
            answer=state["last_answer"],
            language_check_instructions=language_check_instructions,
            next_step_instructions=next_step_instructions,
            next_question_instruction=next_question_instruction,
        )
    )

    qa_entry = {
        "round": round_key,
        "question": state["current_question"],
        "answer": state["last_answer"],
        "score": result.get("score", 5),
        "feedback": result.get("feedback", ""),
        "confidence_flags": result.get("confidence_flags", []),
    }

    conversation = state.get("conversation", []) + [{"role": "candidate", "content": state["last_answer"]}]
    qa_log = state.get("qa_log", []) + [qa_entry]

    update = {
        "conversation": conversation,
        "qa_log": qa_log,
        "last_score": qa_entry["score"],
        "last_feedback": qa_entry["feedback"],
        "last_confidence_flags": qa_entry["confidence_flags"],
    }

    followups_used = state.get("followups_used_on_current_question", 0)
    needs_followup = (
        result.get("needs_followup", False)
        and followups_used < MAX_FOLLOWUPS_PER_QUESTION
    )

    if needs_followup:
        next_q = result.get("followup_question") or "Can you elaborate a bit more on that?"
        update.update({
            "is_followup": True,
            "followups_used_on_current_question": followups_used + 1,
            "questions_asked_in_round": tentative_questions_asked - 1,  # follow-up doesn't consume a question slot
            "current_question": next_q,
            "conversation": conversation + [{"role": "interviewer", "content": next_q}],
        })
        return update

    if not is_last_question_of_round:
        next_q = result.get("next_question") or "Let's move on - tell me about another relevant experience."
        update.update({
            "questions_asked_in_round": tentative_questions_asked,
            "followups_used_on_current_question": 0,
            "is_followup": False,
            "current_question": next_q,
            "conversation": conversation + [{"role": "interviewer", "content": next_q}],
        })
        return update

    if not is_final_round:
        new_index = round_index + 1
        new_round = round_order[new_index]
        next_q = result.get("next_question") or f"Let's move to the {ROUND_LABELS[new_round]} round."
        update.update({
            "round_index": new_index,
            "current_round": new_round,
            "questions_asked_in_round": 0,
            "followups_used_on_current_question": 0,
            "is_followup": False,
            "current_question": next_q,
            "conversation": conversation + [{"role": "interviewer", "content": next_q}],
        })
        return update

    # Final question of the final round - build the report (one more call, unavoidable).
    report = _build_final_report({**state, "qa_log": qa_log})
    update.update({
        "questions_asked_in_round": tentative_questions_asked,
        "final_report": report,
        "finished": True,
    })

    try:
        history.save_completed_interview({**state, **update})
    except Exception:
        logger.exception("Failed to save completed interview to history")

    return update


def route_entry(state: InterviewState) -> str:
    return "turn" if state.get("ingested") else "start"
