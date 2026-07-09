# AI Interview Coach

An AI-powered mock interview simulator. Upload a resume and a job description, and an AI
interviewer runs you through **Behavioral**, **HR**, and **Technical/Coding** rounds — asking
questions out loud, scoring every answer, flagging confidence/communication issues, and producing
a final performance report with an analytics dashboard.

---

## Features

- **Multi-round interview flow** (Behavioral → HR → Coding) driven by a LangGraph state machine
- **RAG-grounded questions** — resume + JD are chunked and embedded locally (ChromaDB +
  sentence-transformers), so questions are grounded in the candidate's actual background and the
  role's actual requirements
- **Voice interview mode** — speak your answers (local Whisper transcription via
  `faster-whisper`, no API key needed) and hear the interviewer's questions read aloud
  (ElevenLabs TTS, with an automatic **free browser-voice fallback** if ElevenLabs is
  unavailable/unconfigured/rate-limited)
- **Live code editor for the coding round** (CodeMirror) supporting **Python, JavaScript, C++,
  and Java**, with strict per-answer language enforcement — code must match the language selected
  in the editor, and prose-only "explanations" are rejected as answers
- **Automatic follow-up questions** when an answer is vague or incomplete
- **Confidence/communication detection** — flags hedging language, filler-heavy phrasing, overly
  short answers, etc.
- **Final report + analytics dashboard** — strengths, areas to improve, per-round breakdown,
  confidence assessment, overall verdict, and score-over-time charts
- **Persistent, per-browser-private interview history** — every completed interview is saved and
  only visible to the browser that ran it (see [Privacy model](#privacy-model) below)
- **Multi-provider LLM failover** — Groq (primary) with automatic fallback to Gemini, and
  automatic retry/cooldown handling across multiple API keys per provider

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, LangGraph, LangChain |
| LLM | Groq (`llama-3.3-70b-versatile`, primary) + Gemini (`gemini-2.5-flash-lite`, backup) |
| RAG | ChromaDB + `sentence-transformers` (`all-MiniLM-L6-v2`), local, no API key needed |
| Speech-to-text | `faster-whisper`, local, no API key needed |
| Text-to-speech | ElevenLabs API, with browser `SpeechSynthesis` fallback |
| Frontend | React 18, Vite, Tailwind CSS, React Router |
| Code editor | CodeMirror 6 (`@uiw/react-codemirror`) — Python / JavaScript / C++ / Java |
| Charts | Recharts |
| History storage | Flat JSON file (`backend/data/history.json`) |

---

## Project structure

```
backend/
  app/
    config.py                # env vars, key parsing, model selection
    state.py                 # LangGraph state schema (InterviewState)
    history.py                # history.json read/write, per-client_id scoping
    graph/
      build.py                # compiles the LangGraph interview graph
      nodes.py                # start_interview_node, process_turn_node
      prompts.py               # all LLM prompt templates
      llm.py                   # multi-provider/multi-key LLM call wrapper
    rag/
      ingest.py                # resume/JD text extraction + chunking + embedding
      registry.py              # in-memory per-session vectorstore registry
    voice/
      stt.py                   # faster-whisper transcription
      tts.py                   # ElevenLabs TTS wrapper
    routes/
      session.py                # /api/session/* endpoints
      history.py                 # /api/history/* endpoints
  main.py                     # FastAPI app + CORS + router registration

frontend/
  src/
    pages/
      UploadScreen.jsx          # resume/JD upload, start interview
      InterviewScreen.jsx       # question/answer loop, voice + code editor
      ReportScreen.jsx          # final report + analytics
      HistoryScreen.jsx         # past interviews list
    components/
      CodeEditor.jsx            # CodeMirror wrapper, language selector
      VoiceRecorder.jsx         # mic recording for voice answers
      ...
    api/
      client.js                 # all backend fetch calls
    utils/
      clientId.js               # anonymous per-browser ID for private history
      transcript.js             # transcript markdown export
    App.jsx                    # route definitions
```

---

## Setup

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:

```bash
# --- LLM (at least one provider required) ---
GROQ_API_KEYS=your_groq_key_here          # comma-separate multiple keys for failover
GROQ_MODEL=llama-3.3-70b-versatile
GOOGLE_API_KEYS=your_gemini_key_here      # optional backup provider
GEMINI_MODEL=gemini-2.5-flash-lite

# --- Voice (optional) ---
ELEVENLABS_API_KEY=your_elevenlabs_key_here
ELEVENLABS_VOICE_ID=your_own_voice_id     # a voice cloned/added to YOUR ElevenLabs
                                           # account - library/premade voices (like the
                                           # default "Rachel") require a paid plan to
                                           # use via the API. If unset/unavailable, the
                                           # app falls back to the browser's built-in
                                           # voice automatically - no key required.
ELEVENLABS_MODEL_ID=eleven_turbo_v2_5

WHISPER_MODEL_SIZE=base                   # tiny/base/small/medium
WHISPER_DEVICE=cpu

# --- Interview settings ---
MAX_QUESTIONS_PER_ROUND=2
MAX_FOLLOWUPS_PER_QUESTION=0
```

Run it:

```bash
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm install @codemirror/lang-cpp @codemirror/lang-java   # C++/Java editor support
npm run dev
```

Open the URL Vite prints (default `http://localhost:5173`).

---

## Privacy model

There's no login system, so history privacy uses a lightweight anonymous identifier instead:
on first visit, the browser generates a random `client_id` (via `crypto.randomUUID()`) and stores
it in `localStorage`. Every interview you start is tagged with it, and `/api/history` only
returns records matching the `client_id` sent in the `X-Client-Id` header.

**This is privacy-by-default, not real authentication.** It stops one person from casually seeing
another's history in a shared deployment, but it's not a security boundary — anyone who copies a
`client_id` out of someone else's browser storage could still read their history. If you need real
access control, replace `client_id` with an authenticated user ID.

---

## Known limitations

- `history.json` is a flat file with a global lock — fine for a small number of users, but not
  built for high concurrent write volume. Swap in SQLite/Postgres if that becomes a problem.
- The in-memory vectorstore registry (`rag/registry.py`) doesn't survive a backend restart and
  won't scale across multiple worker processes.
- Groq/Gemini rate limits are enforced per account/organization, not per key — multiple keys from
  the *same* account share one quota bucket. `GROQ_API_KEYS`/`GOOGLE_API_KEYS` only help if the
  keys are genuinely from separate accounts/projects.
- ElevenLabs free-tier accounts cannot use library/premade voices via the API (only voices
  cloned/added to your own account, or a paid plan) — see the `.env` note above.