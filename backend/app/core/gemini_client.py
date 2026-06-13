import os
import re
import json
import base64
import struct
import asyncio
import random
from functools import lru_cache
from google import genai
from google.genai import types
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_B64_CHARS = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r')

# ── Model Config (overridable via environment/settings) ───────────────────────
FLASH_MODEL      = settings.GEMINI_FLASH_MODEL
PRO_MODEL        = settings.GEMINI_PRO_MODEL
STT_MODEL        = settings.STT_MODEL
STT_LANG         = settings.STT_LANGUAGE
STT_GEMINI_MODEL = settings.STT_GEMINI_MODEL
TTS_GEMINI_MODEL = settings.TTS_GEMINI_MODEL
TTS_GEMINI_VOICE = settings.TTS_GEMINI_VOICE
TTS_LANG         = settings.TTS_LANGUAGE
LIVE_MODEL       = settings.GEMINI_LIVE_MODEL


def _is_mock() -> bool:
    return settings.USE_MOCK_GCP


def coerce_pcm(data) -> bytes:
    """Return raw PCM bytes. Decodes base64 if necessary."""
    if data is None:
        return b""
    if isinstance(data, str):
        data = data.encode("ascii", "ignore")
    sample = data[:4096]
    if sample and all(b in _B64_CHARS for b in sample):
        try:
            return base64.b64decode(data)
        except Exception:
            pass
    return data


def _parse_audio_rate(mime_type: str) -> int:
    """Extract sample rate from mime-type string."""
    m = re.search(r'rate=(\d+)', mime_type or '')
    return int(m.group(1)) if m else 24000


def _pcm_to_wav(pcm: bytes, sample_rate: int = 24000) -> bytes:
    """Wrap raw PCM16 bytes in a WAV container."""
    n = len(pcm)
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', n + 36, b'WAVE',
        b'fmt ', 16, 1, 1, sample_rate,
        sample_rate * 2, 2, 16,
        b'data', n,
    )
    return header + pcm


class MockModels:
    def generate_content(self, model, contents, config=None):
        prompt = ""
        if isinstance(contents, str):
            prompt = contents
        elif isinstance(contents, list):
            prompt = " ".join([str(p) for p in contents])
        
        p = prompt.lower()
        json_mode = False
        if config and config.get("response_mime_type") == "application/json":
            json_mode = True
        elif config and getattr(config, "response_mime_type", None) == "application/json":
            json_mode = True

        text = ""
        if json_mode:
            if "order" in p or "parse" in p:
                text = json.dumps({
                    "customer": "Ramesh Traders",
                    "items": [
                        {"name": "Steel Rods", "quantity": 50, "unit": "rods", "price": 85.0},
                    ],
                    "delivery_date": "tomorrow",
                    "confidence": 0.92,
                    "notes": ""
                })
            elif "ambig" in p or "clarif" in p:
                text = json.dumps({
                    "status": "CLEAR",
                    "ambiguity_type": "",
                    "clarification_question": "",
                    "confidence": 0.95
                })
            elif "collection" in p or "reminder" in p or "due_days" in p:
                text = json.dumps({
                    "risk": "MEDIUM",
                    "risk_score": 0.6,
                    "message": "Namaste ji, aapka invoice number VYP/2024/0003 overdue chal raha hai. Kripya ₹70,800 ka bhugtaan jaldi karein.",
                    "recommended_action": "whatsapp",
                    "follow_up_days": 3,
                })
            elif "ocr" in p or "extract" in p or "document" in p:
                text = json.dumps({
                    "raw_text": "Invoice #VYP/2024/0001 Steel Rods 100 units @ ₹85",
                    "document_type": "invoice",
                    "language": "mixed",
                    "confidence": 0.88,
                    "key_fields": {"amount": "10030"}
                })
            elif "gstr" in p or "validate" in p:
                text = json.dumps({
                    "overall_status": "valid",
                    "issues": [],
                    "suggestions": ["HSN codes valid", "Ready to file"],
                    "filing_ready": True
                })
            else:
                text = json.dumps({"status": "ok", "message": "Mock JSON response"})
        else:
            text = f"Mock Response: I am VyapaarOS assistant. Your prompt was: '{prompt[:40]}...'"

        class MockResponse:
            def __init__(self, text):
                self.text = text
            @property
            def candidates(self):
                class MockCandidate:
                    class MockContent:
                        class MockPart:
                            def __init__(self):
                                class MockBlob:
                                    def __init__(self):
                                        self.data = b"mock audio data"
                                        self.mime_type = "audio/L16;rate=24000"
                                self.inline_data = MockBlob()
                        parts = [MockPart()]
                    content = MockContent()
                return [MockCandidate()]

        return MockResponse(text)


class MockGenAIClient:
    def __init__(self):
        self.models = MockModels()


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client | None:
    """Get the Google GenAI client based on environment configurations."""
    if _is_mock():
        logger.info("Using mock GCP environment. Gemini client will return MockGenAIClient.")
        return MockGenAIClient()

    try:
        if settings.USE_VERTEX_AI:
            client = genai.Client(
                vertexai=True,
                project=settings.GCP_PROJECT_ID,
                location=settings.GCP_LOCATION,
            )
            logger.info("Gemini client initialized with Vertex AI")
            return client
        elif settings.GEMINI_API_KEY:
            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            logger.info("Gemini client initialized with API key")
            return client
        else:
            logger.warning("USE_VERTEX_AI is False, but GEMINI_API_KEY is not set. Attempting default genai.Client initialization.")
            client = genai.Client()
            return client
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        return None


async def generate_text(prompt: str, use_pro: bool = False, json_mode: bool = False, system: str = None) -> str:
    """Generate text from prompt. Falls back to mock if client is not configured."""
    client = get_gemini_client()
    if client is None:
        return await _mock_generate(prompt, json_mode)

    model = PRO_MODEL if use_pro else FLASH_MODEL
    config = {"temperature": 0.3}
    if json_mode:
        config["response_mime_type"] = "application/json"
    if system:
        config["system_instruction"] = system

    def _call():
        return client.models.generate_content(model=model, contents=prompt, config=config)

    try:
        response = await asyncio.to_thread(_call)
        return response.text
    except Exception as e:
        err = str(e)
        logger.error(f"Gemini error: {err}")
        if "503" in err or "UNAVAILABLE" in err:
            return "Gemini AI abhi bahut busy hai — thodi der baad try karein. (Model temporarily overloaded)"
        raise


async def generate_multimodal(parts: list, use_pro: bool = True, json_mode: bool = False, system: str = None) -> str:
    """Generate response from multimodal parts (images/audio/text)."""
    client = get_gemini_client()
    if client is None:
        return json.dumps({
            "raw_text": "Mock OCR extracted text: Sharma Steel Pvt Ltd Invoice #VYP/2024/0001.",
            "document_type": "invoice",
            "language": "mixed",
            "confidence": 0.9,
            "key_fields": {"buyer": "Ramesh Traders", "total": "10030"}
        })

    model = PRO_MODEL if use_pro else FLASH_MODEL
    config = {"temperature": 0.05}
    if json_mode:
        config["response_mime_type"] = "application/json"
    if system:
        config["system_instruction"] = system

    def _call():
        return client.models.generate_content(model=model, contents=parts, config=config)

    response = await asyncio.to_thread(_call)
    return response.text


async def speech_to_text(audio_bytes: bytes, language: str = None, encoding: str = "MP3", mime_type: str = "audio/mp3") -> str:
    """Transcribe audio bytes using Cloud Speech-to-Text with Gemini fallback."""
    lang = language or STT_LANG
    if _is_mock():
        return random.choice([
            "Ramesh ko bol do 50 kilo steel rod chahiye hai kal tak",
            "Suresh ka invoice approved kar do",
            "GST notice explain karo simple Hindi mein",
        ])

    # Try Cloud Speech-to-Text first
    try:
        from google.cloud import speech_v1 as speech
        stt_client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=audio_bytes)
        enc_map = {
            "MP3": speech.RecognitionConfig.AudioEncoding.MP3,
            "LINEAR16": speech.RecognitionConfig.AudioEncoding.LINEAR16,
            "FLAC": speech.RecognitionConfig.AudioEncoding.FLAC,
            "WEBM_OPUS": speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            "OGG_OPUS": speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        }
        config = speech.RecognitionConfig(
            model=STT_MODEL,
            encoding=enc_map.get(encoding, speech.RecognitionConfig.AudioEncoding.MP3),
            language_code=lang,
            alternative_language_codes=["en-IN"],
            enable_automatic_punctuation=True,
        )
        def _call():
            return stt_client.recognize(config=config, audio=audio)
        response = await asyncio.to_thread(_call)
        return " ".join(r.alternatives[0].transcript for r in response.results if r.alternatives)
    except Exception as e:
        logger.warning(f"Cloud Speech-to-Text failed ({e}). Falling back to Gemini audio multimodal transcription.")

    # Gemini fallback
    client = get_gemini_client()
    if client is None:
        return "Audio transcription unavailable (mock mode)"

    def _call():
        return client.models.generate_content(
            model=STT_GEMINI_MODEL,
            contents=[
                types.Part(inline_data=types.Blob(mime_type=mime_type, data=audio_bytes)),
                types.Part(text=f"Transcribe this audio accurately. Language: {lang}. Return only the transcript text, no extra commentary."),
            ],
        )
    response = await asyncio.to_thread(_call)
    return response.text


async def text_to_speech(text: str, language: str = None) -> bytes:
    """Synthesize text to speech using Gemini TTS. Returns WAV bytes."""
    if _is_mock():
        return b""

    client = get_gemini_client()
    if client is None:
        return b""

    lang = language or TTS_LANG

    def _call():
        return client.models.generate_content(
            model=TTS_GEMINI_MODEL,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=TTS_GEMINI_VOICE,
                        )
                    ),
                    language_code=lang,
                ),
            ),
        )

    try:
        response = await asyncio.to_thread(_call)
        part = response.candidates[0].content.parts[0]
        pcm = coerce_pcm(part.inline_data.data)
        rate = _parse_audio_rate(getattr(part.inline_data, 'mime_type', ''))
        logger.info(f"Gemini TTS OK — {len(pcm)} bytes PCM at {rate}Hz")
        return _pcm_to_wav(pcm, rate)
    except Exception as e:
        logger.error(f"Gemini TTS failed: {e}")
        return b""


async def _mock_generate(prompt: str, json_mode: bool) -> str:
    """Generate mock responses for local testing when API credentials are absent."""
    p = prompt.lower()
    if json_mode:
        if "order" in p or "parse" in p:
            return json.dumps({
                "customer": "Ramesh Traders",
                "items": [
                    {"name": "Steel Rods", "quantity": 50, "unit": "rods", "price": 85.0},
                ],
                "delivery_date": "tomorrow",
                "confidence": 0.92,
                "notes": ""
            })
        if "ambig" in p or "clarif" in p:
            return json.dumps({
                "status": "CLEAR",
                "ambiguity_type": "",
                "clarification_question": "",
                "confidence": 0.95
            })
        if "notice" in p or "demand" in p or "penalty" in p or "translate" in p:
            return json.dumps({
                "hindi_translation": "₹57,600 की मांग की गई है। 30 दिनों में भुगतान करें।",
                "notice_type": "DRC-01",
                "action_items": ["30 दिन में भरें", "CA से सलाह लें"],
                "deadline": "2026-07-01",
                "severity": "high",
                "penalty_amount": 4500.0,
                "escalation_required": False,
            })
        if "collection" in p or "reminder" in p or "due_days" in p:
            return json.dumps({
                "risk": "MEDIUM",
                "risk_score": 0.6,
                "message": "Namaste ji, aapka invoice number VYP/2024/0003 overdue chal raha hai. Kripya ₹70,800 ka bhugtaan jaldi karein.",
                "recommended_action": "whatsapp",
                "follow_up_days": 3,
            })
        if "ocr" in p or "extract" in p or "document" in p:
            return json.dumps({
                "raw_text": "Invoice #VYP/2024/0001 Steel Rods 100 units @ ₹85",
                "document_type": "invoice",
                "language": "mixed",
                "confidence": 0.88,
                "key_fields": {"amount": "10030"}
            })
        if "gstr" in p or "validate" in p:
            return json.dumps({
                "overall_status": "valid",
                "issues": [],
                "suggestions": ["HSN codes valid", "Ready to file"],
                "filing_ready": True
            })
        return json.dumps({"status": "ok", "message": "Mock response"})

    return f"Mock Response: I am VyapaarOS assistant. Your prompt: '{prompt[:40]}...'"
