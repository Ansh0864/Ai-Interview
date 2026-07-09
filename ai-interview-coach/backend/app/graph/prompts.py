SUMMARIZE_PROMPT = """You are analyzing a candidate's resume and a job description before an interview.

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

Return ONLY valid JSON with this exact shape, no markdown fences, no preamble:
{{
  "resume_summary": "2-3 sentence summary of the candidate's background",
  "jd_summary": "2-3 sentence summary of what the role requires",
  "key_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"]
}}
"""

# Combines what used to be two separate calls (summarize docs, then generate
# question #1) into one - halves the API calls needed just to start a session.
COMBINED_START_PROMPT = """You are an experienced technical interviewer preparing for a {round_label} round interview.

RESUME:
{resume_text}

JOB DESCRIPTION:
{jd_text}

Relevant context retrieved from the candidate's resume/JD: {retrieved_context}

Instructions for the {round_label} round:
{round_instructions}

Return ONLY valid JSON with this exact shape, no markdown fences, no preamble:
{{
  "resume_summary": "2-3 sentence summary of the candidate's background",
  "jd_summary": "2-3 sentence summary of what the role requires",
  "key_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "first_question": "one clear, specific opening interview question for the {round_label} round"
}}
"""

QUESTION_GENERATION_PROMPT = """You are an experienced technical interviewer conducting a {round_label} round.

Candidate background: {resume_summary}
Role requirements: {jd_summary}
Relevant context retrieved from the candidate's resume/JD: {retrieved_context}

Conversation so far this round:
{round_history}

This is question #{question_number} of {max_questions} in the {round_label} round.

Instructions for this round type:
{round_instructions}

Ask ONE clear, specific interview question. Do not repeat a topic already covered in this round's history.
Return ONLY the question text, nothing else - no numbering, no preamble.
"""

FOLLOWUP_PROMPT = """You are an interviewer in a {round_label} round. The candidate just answered:

Question: {current_question}
Answer: {last_answer}

The answer was somewhat vague, incomplete, or you want to probe deeper based on something specific they said.
Ask ONE natural, specific follow-up question that digs into a detail from their actual answer.
Return ONLY the follow-up question text, nothing else.
"""

SCORING_PROMPT = """You are scoring a candidate's interview answer.

Round: {round_label}
Question: {question}
Candidate's answer: {answer}

Evaluate on: relevance, specificity/concrete examples, clarity, and (if coding round) technical correctness.

Also flag confidence/communication issues if present, by looking for:
- hedging language ("I think maybe", "I'm not sure but", "probably", excessive qualifiers)
- very short or vague answers relative to the question's complexity
- filler-heavy phrasing
- avoidance of directly answering the question

Return ONLY valid JSON, no markdown fences:
{{
  "score": <integer 1-10>,
  "feedback": "2-3 sentences of specific, constructive feedback",
  "confidence_flags": ["flag1", "flag2"],
  "needs_followup": <true or false, true only if the answer is vague/incomplete and worth probing>
}}
"""

# Combines scoring + deciding-next-step + generating the next question into
# ONE call (previously 2 separate calls per turn). The model produces both
# a possible follow-up AND a possible fresh/next-round question in the same
# response; Python then picks whichever one applies based on needs_followup
# and round bookkeeping it already knows deterministically.
COMBINED_TURN_PROMPT = """You are an interviewer conducting a {round_label} round.

Candidate background: {resume_summary}
Role requirements: {jd_summary}

Question asked: {question}
Candidate's answer: {answer}
{language_check_instructions}
Evaluate the answer on: relevance, specificity/concrete examples, clarity, and (if coding round) technical correctness.
Also flag confidence/communication issues if present (hedging language, very short/vague answers, filler-heavy phrasing, avoidance).

{next_step_instructions}

Return ONLY valid JSON, no markdown fences, no preamble:
{{
  "score": <integer 1-10>,
  "feedback": "2-3 sentences of specific, constructive feedback on THIS answer",
  "confidence_flags": ["flag1", "flag2"],
  "needs_followup": <true or false, true only if the answer is vague/incomplete and genuinely worth probing further>,
  "followup_question": "a natural follow-up question digging into a specific detail of their answer - write this regardless of needs_followup, it's simply ignored if not needed",
  "next_question": "{next_question_instruction}"
}}
"""

LANGUAGE_CHECK_INSTRUCTIONS = """
IMPORTANT: The candidate selected "{declared_language}" as their language for this code answer.
This selection is a strict requirement, not a suggestion - the candidate must submit code written
in exactly this language.

STEP 1 - Is this actually code? Check whether the submission is real source code (function/method
definitions, correct block structure, variable declarations, operators, etc.) as opposed to a
prose paragraph that merely DESCRIBES an approach in plain English ("I would first loop through
the array and check...") without ever writing actual syntax. A written explanation, however
correct or well-reasoned, is NOT a substitute for code. If the submission is prose with no real
code in it, cap the score at 2/10 and say so explicitly in the feedback.

STEP 2 - Only if real code IS present: identify which language it is ACTUALLY written in by its
syntax, keywords, and conventions - do not just trust the declared_language label. Rough tells:
Python uses indentation-based blocks, `def`, `:`, no semicolons or curly braces. C++ uses
`#include`, `int main()`, explicit types, semicolons, curly braces. Java uses `public class`,
`public static void main`, explicit types, semicolons, curly braces. JavaScript/TypeScript uses
`function`/`=>`, `let`/`const`/`var`, curly braces, optional semicolons.

If the code you detect does NOT match "{declared_language}" (e.g. Python was selected but the
code is written in C++ or Java syntax, or C++ was selected but the code is Python), this is a
strict instruction-following failure regardless of how correct or elegant the logic is: cap the
score at 3/10, and explicitly state in the feedback which language you actually detected versus
which one was selected, and that they need to resubmit their answer in the correct language field.

Only if the code is genuine AND its syntax correctly matches "{declared_language}" should you
evaluate normally on correctness, edge cases, time/space complexity, and code quality.
"""

NEXT_STEP_SAME_ROUND = """This is question #{question_number} of {max_questions} in the {round_label} round.
If a follow-up isn't needed, the interview continues with a NEW question in the SAME {round_label} round.
Round context so far:
{round_history}

Instructions for the {round_label} round:
{round_instructions}"""

NEXT_STEP_NEW_ROUND = """This was the LAST question of the {round_label} round.
If a follow-up isn't needed, the interview moves on to the {next_round_label} round - "next_question" should be
the OPENING question of that new round, not a continuation of {round_label}.

Instructions for the {next_round_label} round:
{next_round_instructions}"""

NEXT_STEP_FINAL = """This was the LAST question of the FINAL round ({round_label}) - the interview is ending.
If a follow-up isn't needed, set "next_question" to an empty string "" since there's nothing more to ask."""

FINAL_REPORT_PROMPT = """You are compiling a final interview performance report.

Candidate background: {resume_summary}
Role: {jd_summary}

Full Q&A log with scores:
{qa_summary}

Return ONLY valid JSON, no markdown fences:
{{
  "overall_score": <integer 1-10, weighted average impression>,
  "strengths": ["strength1", "strength2", "strength3"],
  "areas_to_improve": ["area1", "area2", "area3"],
  "round_breakdown": {{
    "behavioral": "1-2 sentence assessment",
    "hr": "1-2 sentence assessment",
    "coding": "1-2 sentence assessment"
  }},
  "confidence_assessment": "2-3 sentences on communication style/confidence patterns observed across the interview",
  "final_verdict": "2-3 sentence overall hiring-readiness summary"
}}
"""

ROUND_INSTRUCTIONS = {
    "behavioral": "Ask about past experiences, teamwork, conflict resolution, ownership, and decision-making using a STAR-style prompt (e.g. 'Tell me about a time when...').",
    "hr": "Ask about motivation, career goals, culture fit, salary expectations, why this role/company, and strengths/weaknesses.",
    "coding": (
        "Ask a genuine written coding problem that REQUIRES the candidate to submit actual code "
        "as the answer (there's a live code editor with language selection - this is not a "
        "text-only round). Do NOT ask something that can be fully answered with a prose "
        "explanation alone. Alternate between two problem sources: (a) a classic DSA problem "
        "appropriate for a CS new-grad role (arrays/strings, hashmaps, two pointers, trees, "
        "graphs, recursion/DP, sorting/searching) at easy-to-medium difficulty, or (b) a "
        "practical coding problem grounded in the specific technologies/stack mentioned in the "
        "job description (e.g. write a function/endpoint/component that does X using the JD's "
        "stack). State the problem clearly, including a short example input and expected output "
        "so the candidate knows exactly what to implement. Since there's no live code execution, "
        "the candidate's code will be read and evaluated for correctness and quality, not run."
    ),
}

ROUND_LABELS = {
    "behavioral": "Behavioral",
    "hr": "HR",
    "coding": "Technical/Coding",
}