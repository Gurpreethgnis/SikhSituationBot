"""
voice_routes.py — Flask blueprint for voice STT and TTS.

Endpoints:
  POST /api/voice/transcribe   — Audio blob → Whisper transcript
  POST /api/voice/synthesize   — Text → Streaming TTS audio/mpeg
  GET  /api/voice/config       — Supported languages / voices metadata

Hard constraints respected:
  - Audio is NEVER written to disk; all processing uses in-memory BytesIO buffers.
  - This blueprint does NOT touch any existing chat routes, system prompts,
    Gurbani logic, session handling, or database tables.
  - All errors are contained here and do not affect /ask or any other route.
"""

import io
import logging
import os

from flask import Blueprint, Response, jsonify, request, stream_with_context

logger = logging.getLogger(__name__)

voice_blueprint = Blueprint("voice", __name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES = [
    {"code": "en", "label": "English"},
    {"code": "pa", "label": "ਪੰਜਾਬੀ (Punjabi)"},
    {"code": "hi", "label": "हिंदी (Hindi)"},
    {"code": "zh", "label": "中文 (Chinese)"},
    {"code": "es", "label": "Español"},
    {"code": "fr", "label": "Français"},
    {"code": "ar", "label": "العربية"},
    {"code": "pt", "label": "Português"},
    {"code": "ru", "label": "Русский"},
]

AVAILABLE_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

# Max audio size accepted (25 MB — Whisper API limit)
MAX_AUDIO_BYTES = 25 * 1024 * 1024

# pydub is optional; if ffmpeg is absent we pass audio directly to Whisper
_PYDUB_AVAILABLE = False
try:
    from pydub import AudioSegment  # noqa: F401

    _PYDUB_AVAILABLE = True
except Exception:
    logger.warning(
        "pydub is not available or ffmpeg is missing — "
        "audio format conversion disabled; webm/wav/mp3 are passed directly to Whisper."
    )


def _get_openai_client():
    """Lazy-initialise the OpenAI client so import-time failures don't crash the app."""
    try:
        import openai  # noqa: PLC0415

        return openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    except Exception as exc:
        logger.error("Failed to create OpenAI client: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Helper: convert audio to wav in-memory if pydub+ffmpeg are available
# ---------------------------------------------------------------------------


def _to_wav_bytes(raw: bytes, mime: str) -> tuple[bytes, str]:
    """
    Attempt to convert raw audio bytes to wav using pydub.
    Returns (bytes, filename_extension) — falls back to original if conversion fails.
    """
    if not _PYDUB_AVAILABLE:
        return raw, _mime_to_ext(mime)

    fmt_map = {
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "audio/mp4": "mp4",
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/wav": "wav",
        "audio/x-wav": "wav",
    }
    fmt = fmt_map.get(mime, "webm")
    if fmt == "wav":
        return raw, "wav"

    try:
        from pydub import AudioSegment  # noqa: PLC0415

        seg = AudioSegment.from_file(io.BytesIO(raw), format=fmt)
        buf = io.BytesIO()
        seg.export(buf, format="wav")
        return buf.getvalue(), "wav"
    except Exception as exc:
        logger.warning("pydub conversion failed (%s) — passing raw bytes to Whisper: %s", fmt, exc)
        return raw, fmt


def _mime_to_ext(mime: str) -> str:
    return {
        "audio/webm": "webm",
        "audio/ogg": "ogg",
        "audio/mp4": "mp4",
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3",
        "audio/wav": "wav",
        "audio/x-wav": "wav",
    }.get(mime, "webm")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@voice_blueprint.route("/api/voice/config", methods=["GET"])
def voice_config():
    """Return supported languages, available TTS voices, and VAD capability flag."""
    return jsonify(
        {
            "supported_languages": SUPPORTED_LANGUAGES,
            "available_voices": AVAILABLE_VOICES,
            "vad_enabled": True,
        }
    ), 200


@voice_blueprint.route("/api/voice/transcribe", methods=["POST"])
def transcribe_audio():
    """
    Accept an audio blob (multipart/form-data) and return a Whisper transcript.

    Form fields:
      audio    — binary audio file (required)
      language — BCP-47 language hint, e.g. "en" or "pa" (optional, default "en")

    Returns:
      200 { transcript: str, confidence: float, language: str }
      400 { error: "empty_audio" }
      400 { error: "transcription_failed", message: str }
      503 { error: "voice_unavailable", message: str }
    """
    audio_file = request.files.get("audio")
    language = (request.form.get("language") or "en").strip()

    # --- Validate input ---
    if not audio_file or audio_file.filename == "":
        return jsonify({"error": "empty_audio"}), 400

    raw_bytes = audio_file.read()
    if not raw_bytes or len(raw_bytes) < 512:
        return jsonify({"error": "empty_audio"}), 400

    if len(raw_bytes) > MAX_AUDIO_BYTES:
        return jsonify({"error": "audio_too_large", "max_mb": 25}), 400

    mime = audio_file.content_type or "audio/webm"

    # --- Convert if possible ---
    audio_bytes, ext = _to_wav_bytes(raw_bytes, mime)

    # --- Call Whisper via OpenAI SDK ---
    client = _get_openai_client()
    if client is None:
        return jsonify({"error": "voice_unavailable", "message": "OpenAI client could not be initialised"}), 503

    try:
        # Whisper expects a file-like object with a .name attribute
        audio_buf = io.BytesIO(audio_bytes)
        audio_buf.name = f"audio.{ext}"

        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buf,
            language=language if language != "en" else None,  # omit for English (auto-detect)
            response_format="verbose_json",
        )

        transcript = (response.text or "").strip()
        if not transcript:
            return jsonify({"error": "transcription_failed", "message": "Whisper returned an empty transcript"}), 400

        # verbose_json may include avg_logprob; map to a 0–1 confidence estimate
        confidence = 1.0
        try:
            if hasattr(response, "segments") and response.segments:
                logprobs = [s.get("avg_logprob", 0) for s in response.segments if isinstance(s, dict)]
                if logprobs:
                    import math

                    avg = sum(logprobs) / len(logprobs)
                    confidence = round(min(1.0, max(0.0, math.exp(avg))), 3)
        except Exception:
            pass  # confidence is a nice-to-have; don't fail the request

        detected_language = getattr(response, "language", language) or language

        return jsonify(
            {
                "transcript": transcript,
                "confidence": confidence,
                "language": detected_language,
            }
        ), 200

    except Exception as exc:
        logger.error("Whisper transcription failed: %s", exc)
        return jsonify({"error": "transcription_failed", "message": str(exc)}), 400


@voice_blueprint.route("/api/voice/synthesize", methods=["POST"])
def synthesize_speech():
    """
    Accept JSON { text, voice? } and stream TTS audio/mpeg back to the client.
    Uses tts-1 (speed-optimised). Does NOT buffer the full audio before sending.

    Returns:
      200 audio/mpeg streaming response
      400 { error: "text_required" }
      503 { error: "voice_unavailable", message: str }
    """
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    voice = (data.get("voice") or "alloy").strip().lower()

    if not text:
        return jsonify({"error": "text_required"}), 400

    if voice not in AVAILABLE_VOICES:
        voice = "alloy"

    # Truncate to OpenAI TTS limit (4096 chars)
    text = text[:4096]

    client = _get_openai_client()
    if client is None:
        return jsonify({"error": "voice_unavailable", "message": "OpenAI client could not be initialised"}), 503

    def generate():
        try:
            with client.audio.speech.with_streaming_response.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3",
            ) as tts_response:
                for chunk in tts_response.iter_bytes(chunk_size=4096):
                    if chunk:
                        yield chunk
        except Exception as exc:
            logger.error("TTS synthesis failed: %s", exc)
            # Yield nothing on error — client will see an empty/truncated stream.
            # The frontend handles this via the SPEAKING → error → IDLE transition.

    return Response(
        stream_with_context(generate()),
        content_type="audio/mpeg",
        headers={
            "Cache-Control": "no-cache, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
