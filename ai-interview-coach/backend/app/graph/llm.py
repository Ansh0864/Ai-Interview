import json
import re
import time
import threading
from typing import Optional, List, Tuple
import groq
from google.api_core import exceptions as google_exceptions
from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
import logging
from app.config import GROQ_API_KEYS, GROQ_MODEL, GOOGLE_API_KEYS, GEMINI_MODEL

logger = logging.getLogger("interview_coach.llm")


class ModelUnavailableError(Exception):
    """Raised when a configured model/key is invalid for EVERY provider -
    retrying will never help here, unlike a genuine rate limit."""
    pass


class RateLimitExceeded(Exception):
    """
    Raised when every configured key across every configured provider is
    currently rate-limited. Carries the exact wait time until the SOONEST
    slot becomes available again, so the frontend can show a real countdown.
    """
    def __init__(self, message: str, retry_after_seconds: Optional[float] = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


# --- Provider + multi-key failover --------------------------------------
# Groq is tried first (faster, higher free-tier throughput); Gemini is an
# optional backup tried only once every configured Groq key is exhausted.
# CAVEAT that applies to BOTH providers: rate limits are enforced per
# account/project, not per key - multiple keys from the SAME account only
# help if they're each from genuinely separate accounts/projects.
Slot = Tuple[str, int]  # (provider_name, key_index within that provider's key list)

_PROVIDER_KEYS = {"groq": GROQ_API_KEYS, "gemini": GOOGLE_API_KEYS}
_PROVIDER_MODEL = {"groq": GROQ_MODEL, "gemini": GEMINI_MODEL}

# Priority order: every Groq key first, then every Gemini key.
_ALL_SLOTS: List[Slot] = (
    [("groq", i) for i in range(len(GROQ_API_KEYS))]
    + [("gemini", i) for i in range(len(GOOGLE_API_KEYS))]
)

_llm_cache = {}
_cooldowns = {}  # Slot -> epoch timestamp until which to avoid this slot
_lock = threading.Lock()

_MIN_INTERVAL_SECONDS = 0.3
_last_call_time = 0.0


def _pace_call():
    global _last_call_time
    with _lock:
        elapsed = time.monotonic() - _last_call_time
        if elapsed < _MIN_INTERVAL_SECONDS:
            time.sleep(_MIN_INTERVAL_SECONDS - elapsed)
        _last_call_time = time.monotonic()


def get_llm(slot: Slot, temperature: float):
    provider, key_index = slot
    cache_key = (provider, key_index, round(temperature, 2))
    if cache_key not in _llm_cache:
        key = _PROVIDER_KEYS[provider][key_index]
        if provider == "groq":
            _llm_cache[cache_key] = ChatGroq(
                model=_PROVIDER_MODEL["groq"], groq_api_key=key, temperature=temperature,
            )
        else:
            _llm_cache[cache_key] = ChatGoogleGenerativeAI(
                model=_PROVIDER_MODEL["gemini"], google_api_key=key, temperature=temperature,
            )
    return _llm_cache[cache_key]


def _extract_retry_delay(exc: Exception) -> Optional[float]:
    """
    Groq exposes the real HTTP 'retry-after' header on exc.response - prefer
    that. Otherwise fall back to parsing either provider's error text:
    Groq-style "in 6m 11.52s" / "in 45.98s", or Gemini-style "retry in 37.7s".
    """
    response = getattr(exc, "response", None)
    if response is not None:
        header_value = getattr(response, "headers", {}).get("retry-after")
        if header_value:
            try:
                return float(header_value)
            except ValueError:
                pass

    text = str(exc)
    match = re.search(r"in (?:(\d+)m\s*)?(\d+(?:\.\d+)?)s", text, re.IGNORECASE)
    if match:
        minutes = float(match.group(1)) if match.group(1) else 0.0
        return minutes * 60 + float(match.group(2))

    match = re.search(r"retry in (\d+(?:\.\d+)?)s?", text, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def _mark_exhausted(slot: Slot, exc: Exception):
    cooldown = _extract_retry_delay(exc) or 30
    logger.warning(f"{slot[0]} key #{slot[1]} rate-limited - unavailable for {cooldown:.1f}s.")
    with _lock:
        _cooldowns[slot] = time.time() + cooldown


def _available_slots() -> List[Slot]:
    now = time.time()
    return [s for s in _ALL_SLOTS if _cooldowns.get(s, 0) <= now]


def _soonest_cooldown_remaining() -> float:
    now = time.time()
    if not _ALL_SLOTS:
        return 0
    return max(0.0, min(_cooldowns.get(s, 0) for s in _ALL_SLOTS) - now)


def call_llm_text(prompt: str, temperature: float = 0.7) -> str:
    """
    Tries every available (provider, key) slot in priority order - all Groq
    keys first, then all Gemini keys as backup - skipping any currently in
    cooldown. Raises RateLimitExceeded (with an honest retry_after_seconds)
    only once every slot across every provider has been tried and failed.
    """
    if not _ALL_SLOTS:
        raise RuntimeError(
            "No LLM API key configured. Set GROQ_API_KEY in backend/.env "
            "(and optionally GOOGLE_API_KEY as a backup)."
        )

    available = _available_slots()
    if not available:
        raise RateLimitExceeded(
            f"All {len(_ALL_SLOTS)} configured key(s) across all providers are currently rate-limited.",
            retry_after_seconds=_soonest_cooldown_remaining(),
        )

    last_exc = None
    for slot in available:
        provider, key_index = slot
        _pace_call()
        try:
            response = get_llm(slot, temperature).invoke(prompt)
            return response.content.strip()
        except (groq.NotFoundError, google_exceptions.NotFound) as e:
            logger.warning(f"{provider} model not found/unavailable - skipping this provider for the rest of this call.")
            last_exc = e
            continue
        except (groq.AuthenticationError, google_exceptions.PermissionDenied, google_exceptions.Unauthenticated) as e:
            logger.warning(f"{provider} key #{key_index} rejected (auth error) - skipping to next available key/provider.")
            last_exc = e
            continue
        except (groq.RateLimitError, google_exceptions.ResourceExhausted) as e:
            _mark_exhausted(slot, e)
            last_exc = e
            continue

    raise RateLimitExceeded(
        f"{last_exc}\nAll configured provider(s)/key(s) are exhausted or rejected.",
        retry_after_seconds=_soonest_cooldown_remaining(),
    )


def call_llm_json(prompt: str, temperature: float = 0.3) -> dict:
    """
    Calls the LLM expecting a JSON object back. Robustly extracts JSON
    even if the model includes extra conversational text around it.
    """
    raw = call_llm_text(prompt, temperature=temperature)
    cleaned = re.sub(
        r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE
    ).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        raise ValueError(
            f"Could not parse valid JSON from LLM response: {raw[:300]}"
        )
