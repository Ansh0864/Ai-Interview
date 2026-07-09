import requests
from app.config import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL_ID

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"


class TTSError(Exception):
    """Raised for an actual API failure (bad key, quota, bad voice/model ID, etc).
    Carries the real HTTP status so the caller can distinguish a genuine
    ElevenLabs error from "not configured at all"."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code



class TTSNotConfigured(Exception):
    
    """Raised specifically when no API key is set at all - distinct from
    TTSError so the frontend can tell 'you haven't set a key' apart from
    'your key/voice/model is wrong', which previously showed identically."""
    pass


def synthesize_speech(text: str) -> bytes:
    """Returns raw MP3 bytes for the given text, spoken by the interviewer voice."""
    if not ELEVENLABS_API_KEY:
        raise TTSNotConfigured("ELEVENLABS_API_KEY is not set in backend/.env.")


    url = ELEVENLABS_TTS_URL.format(voice_id=ELEVENLABS_VOICE_ID)
    try:
        response = requests.post(
            url,
            headers={
                "xi-api-key": ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },


            json={

                "text": text,
                "model_id": ELEVENLABS_MODEL_ID,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=30,
        )
    except requests.RequestException as e:

        raise TTSError(f"Could not reach ElevenLabs: {e}", status_code=502)



    if response.status_code == 401:


        raise TTSError(
            "ElevenLabs rejected the API key (401 Unauthorized). Double-check "
            "ELEVENLABS_API_KEY in backend/.env is correct and has no extra "
            "spaces/quotes, and that the backend was restarted after editing .env.",
            status_code=401,
        )
    

    if response.status_code == 402:


        raise TTSError(
            "ElevenLabs free-tier accounts can't use library/premade voices (like the "
            "default 'Rachel' voice) through the API - only voices cloned/added to your "
            "own account, or a paid plan, work via the API. Add a voice under 'My Voices' "
            "in your ElevenLabs account and set ELEVENLABS_VOICE_ID to it, or upgrade your "
            "plan. Falling back to the browser's built-in voice for now.",
          
          
            status_code=402,
        )
    if response.status_code == 429:
        raise TTSError(
            "ElevenLabs quota/rate limit exceeded (429) - check usage at "
            "https://elevenlabs.io/app/usage.",
            status_code=429,
        )
    if response.status_code != 200:
        raise TTSError(
            f"ElevenLabs error {response.status_code}: {response.text[:300]}",
            status_code=response.status_code,
        )



    return response.content