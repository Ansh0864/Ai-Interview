import os
from dotenv import load_dotenv

_dotenv_path = load_dotenv()
print(f"[INFO] .env loaded from: {_dotenv_path or 'NOT FOUND - check the file is really named .env, not .env.txt'}")



def _mask(key: str) -> str:
    if not key:
        return "(empty)"
    return f"{key[:4]}...{key[-4:]} (length {len(key)})"


def _parse_keys(env_var_plural: str, env_var_singular: str) -> list:
    raw = os.getenv(env_var_plural, "") or os.getenv(env_var_singular, "")
    return [k.strip() for k in raw.split(",") if k.strip()]


# --- Primary provider: Groq -------------------------------------------
# Supports multiple keys for failover: GROQ_API_KEYS="key1,key2"
# CAVEAT (confirmed from Groq's own docs): rate limits are enforced PER
# ORGANIZATION/ACCOUNT, not per API key - two keys from the same Groq
# account share one quota bucket. See README "Rate limits".


GROQ_API_KEYS = _parse_keys("GROQ_API_KEYS", "GROQ_API_KEY")
GROQ_API_KEY = GROQ_API_KEYS[0] if GROQ_API_KEYS else ""
print(f"[INFO] Groq key(s) loaded: {[_mask(k) for k in GROQ_API_KEYS] or 'NONE'}")


# llama-3.3-70b-versatile: 30 RPM, ~1,000 requests/day, strongest quality.
# llama-3.1-8b-instant: 30 RPM, ~14,400 requests/day - far more headroom.


GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")



# --- Backup provider: Gemini --------------------------------------------
# Optional. If set, the app falls back to Gemini automatically once every
# configured Groq key is rate-limited/exhausted, instead of failing the
# request outright. Same per-project caveat as Groq has per-organization:
# GOOGLE_API_KEYS="key1,key2" only helps with keys from separate projects.



GOOGLE_API_KEYS = _parse_keys("GOOGLE_API_KEYS", "GOOGLE_API_KEY")
GOOGLE_API_KEY = GOOGLE_API_KEYS[0] if GOOGLE_API_KEYS else ""
print(f"[INFO] Gemini backup key(s) loaded: {[_mask(k) for k in GOOGLE_API_KEYS] or 'NONE (no backup provider configured)'}")




# gemini-2.0-flash was deprecated June 1, 2026. gemini-2.5-flash's free
# tier is ~20 requests/DAY (very low); gemini-2.5-flash-lite gets ~1,000/day.


GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
MAX_QUESTIONS_PER_ROUND = int(os.getenv("MAX_QUESTIONS_PER_ROUND", "2"))
MAX_FOLLOWUPS_PER_QUESTION = int(os.getenv("MAX_FOLLOWUPS_PER_QUESTION", "0"))



if not GROQ_API_KEYS and not GOOGLE_API_KEYS:

    print("[WARNING] No LLM API key set at all. Add GROQ_API_KEY (and optionally GOOGLE_API_KEY as backup) to backend/.env.")



# --- Persistent interview history ---------------------------------------


HISTORY_FILE = os.getenv("HISTORY_FILE", "./data/history.json")


# --- Voice (Phase 2) ---

# Whisper runs locally via faster-whisper, so no API key needed for STT

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")  # tiny/base/small/medium
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")



# ElevenLabs TTS does need a key.

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # "Rachel", ElevenLabs' default demo voice
ELEVENLABS_MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5")
print(f"[INFO] ElevenLabs key loaded: {_mask(ELEVENLABS_API_KEY)}")



VOICE_ENABLED = bool(ELEVENLABS_API_KEY)
if not ELEVENLABS_API_KEY:
    print("[INFO] ELEVENLABS_API_KEY not set - TTS endpoint will return 503 until you add one.")
