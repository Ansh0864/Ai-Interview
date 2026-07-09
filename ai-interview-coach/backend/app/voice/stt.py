import io
import tempfile
import os
from typing import Optional
from faster_whisper import WhisperModel
from app.config import WHISPER_MODEL_SIZE, WHISPER_DEVICE

_model: Optional[WhisperModel] = None

def get_model() -> WhisperModel:
    global _model
    if _model is None:
        compute_type = "int8" if WHISPER_DEVICE == "cpu" else "float16"
        _model = WhisperModel(WHISPER_MODEL_SIZE, device=WHISPER_DEVICE, compute_type=compute_type)
    return _model


def transcribe_audio(audio_bytes: bytes, filename_hint: str = "audio.webm") -> str:
    """
    Writes the uploaded audio to a temp file (faster-whisper reads via
    ffmpeg under the hood, so it needs a real file path, not raw bytes)
    and returns the transcribed text.
    """
    suffix = os.path.splitext(filename_hint)[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, _info = get_model().transcribe(tmp_path, beam_size=5, language="en")
        return " ".join(segment.text.strip() for segment in segments).strip()
    finally:
        os.unlink(tmp_path)
