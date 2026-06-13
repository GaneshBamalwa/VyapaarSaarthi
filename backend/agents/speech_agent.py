"""
Speech Agent — transcribes audio to text.
Primary: Cloud Speech-to-Text (chirp_2, hi-IN).
Fallback: Gemini multimodal audio transcription.
"""
import time
from utils.gemini_client import speech_to_text
from utils.ws_manager import ws_manager

AUDIO_MIME_TO_ENCODING = {
    "audio/mpeg": "MP3",
    "audio/mp3":  "MP3",
    "audio/wav":  "LINEAR16",
    "audio/flac": "FLAC",
    "audio/ogg":  "OGG_OPUS",
    "audio/webm": "WEBM_OPUS",
}


async def run(audio_bytes: bytes, language: str = "hi-IN",
              mime_type: str = "audio/mp3", order_id: int = None) -> dict:
    await ws_manager.emit_agent_event("SpeechAgent", "running", "transcribing_audio", order_id=order_id)
    start = time.time()
    try:
        encoding = AUDIO_MIME_TO_ENCODING.get(mime_type, "MP3")
        transcript = await speech_to_text(
            audio_bytes=audio_bytes,
            language=language,
            encoding=encoding,
            mime_type=mime_type,
        )
        duration_ms = int((time.time() - start) * 1000)
        await ws_manager.emit_agent_event(
            "SpeechAgent", "completed", "audio_transcribed",
            data={"transcript_length": len(transcript)}, order_id=order_id,
        )
        return {"status": "success", "agent": "SpeechAgent",
                "data": {"transcript": transcript, "language_code": language},
                "duration_ms": duration_ms}
    except Exception as e:
        await ws_manager.emit_agent_event("SpeechAgent", "failed", "transcription_error",
                                          error=str(e), order_id=order_id)
        return {"status": "error", "agent": "SpeechAgent", "error": str(e)}
