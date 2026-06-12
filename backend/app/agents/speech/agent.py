import time
from typing import Any

from app.agents.base import BaseAgent
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


class SpeechAgent(BaseAgent):
    name = "SpeechAgent"

    async def invoke(self, input_data: dict, **kwargs) -> dict[str, Any]:
        """
        input_data: {
            "audio_bytes": bytes,
            "encoding": str,  # LINEAR16, FLAC, MP3, WEBM_OPUS
            "sample_rate": int,
            "language_code": str  # hi-IN default
        }
        """
        audio_bytes = input_data.get("audio_bytes", b"")
        language_code = input_data.get("language_code", settings.VERTEX_SPEECH_LANGUAGE)
        encoding = input_data.get("encoding", "MP3")
        sample_rate = input_data.get("sample_rate", 16000)
        mime_type = input_data.get("mime_type", "audio/mp3")
        order_id = kwargs.get("order_id")

        await self._emit("running", "transcribing_audio", order_id=order_id)
        start = time.time()

        try:
            transcript = await self._transcribe_vertex(
                audio_bytes=audio_bytes,
                encoding=encoding,
                sample_rate=sample_rate,
                language_code=language_code,
                mime_type=mime_type,
            )

            duration_ms = int((time.time() - start) * 1000)
            await self._emit(
                "completed",
                "audio_transcribed",
                data={"transcript_length": len(transcript)},
                order_id=order_id,
            )

            return self._success(
                {"transcript": transcript, "language_code": language_code},
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"SpeechAgent error: {e}")
            await self._emit("failed", "transcription_error", error=str(e), order_id=order_id)
            return self._failure(str(e))

    async def _transcribe_vertex(
        self,
        audio_bytes: bytes,
        encoding: str,
        sample_rate: int,
        language_code: str,
        mime_type: str = "audio/mp3",
    ) -> str:
        """Use Google Cloud Speech-to-Text via google-cloud-speech."""
        try:
            from google.cloud import speech_v1
            import base64

            client = speech_v1.SpeechClient()

            audio = speech_v1.RecognitionAudio(content=audio_bytes)
            config = speech_v1.RecognitionConfig(
                encoding=getattr(speech_v1.RecognitionConfig.AudioEncoding, encoding, speech_v1.RecognitionConfig.AudioEncoding.MP3),
                sample_rate_hertz=sample_rate,
                language_code=language_code,
                alternative_language_codes=["en-IN"],
                enable_automatic_punctuation=True,
            )

            response = client.recognize(config=config, audio=audio)
            transcript = " ".join(
                result.alternatives[0].transcript
                for result in response.results
                if result.alternatives
            )
            return transcript

        except Exception as e:
            logger.warning(f"Vertex AI Speech-to-Text failed or not configured, falling back to Gemini: {e}")
            # Fallback: use Gemini for audio transcription
            return await self._transcribe_gemini(audio_bytes, language_code, mime_type)

    async def _transcribe_gemini(self, audio_bytes: bytes, language_code: str, mime_type: str = "audio/mp3") -> str:
        """Fallback transcription using Gemini."""
        import base64
        from app.core.gemini_client import get_gemini_client

        client = get_gemini_client()
        audio_b64 = base64.b64encode(audio_bytes).decode()

        # Ensure we pass a mime type that Gemini supports
        if not mime_type or not mime_type.startswith("audio/"):
            mime_type = "audio/mp3"

        response = client.models.generate_content(
            model=settings.GEMINI_FLASH_MODEL,
            contents=[
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": audio_b64,
                            }
                        },
                        {
                            "text": f"Transcribe this audio accurately. Language: {language_code}. Return only the transcript text."
                        },
                    ]
                }
            ],
        )
        return response.text.strip()
