"""
Unified Gemini / Vertex AI client.

Priority order (set in .env):
  1. USE_MOCK_GCP=true         → mock responses, no credentials needed
  2. GEMINI_API_KEY=...        → Google AI Studio (fast, free-tier, great for testing)
  3. USE_VERTEX_AI=true + GCP  → Vertex AI via ADC (production)

All model names are env-configurable — change them without touching code.
"""
import os
import re
import json
import base64
import struct
import asyncio
import random
from functools import lru_cache

# Base64 alphabet bytes — used to detect when Vertex returns audio still-encoded
_B64_CHARS = set(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=\n\r')


def coerce_pcm(data) -> bytes:
    """Return raw PCM bytes.

    Vertex AI (vertexai=True) often returns inline_data.data as base64-ENCODED
    bytes/str rather than decoded PCM. Raw PCM16 contains null bytes and values
    across the full 0-255 range, so if every byte falls inside the base64
    alphabet, the payload is still encoded — decode it.
    """
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

# ── Model config (all overridable via .env) ────────────────────────────────
FLASH_MODEL      = os.getenv("GEMINI_FLASH_MODEL",  "gemini-2.5-flash")
PRO_MODEL        = os.getenv("GEMINI_PRO_MODEL",    "gemini-2.5-pro")
STT_MODEL        = os.getenv("STT_MODEL",            "chirp_2")
STT_LANG         = os.getenv("STT_LANGUAGE",         "hi-IN")
STT_GEMINI_MODEL = os.getenv("STT_GEMINI_MODEL",    "gemini-2.5-flash")
TTS_GEMINI_MODEL = os.getenv("TTS_GEMINI_MODEL",    "gemini-2.5-flash-preview-tts")
TTS_GEMINI_VOICE = os.getenv("TTS_GEMINI_VOICE",    "Aoede")
TTS_LANG         = os.getenv("TTS_LANGUAGE",         "hi-IN")

# Live model for Gemini bidirectional streaming
LIVE_MODEL       = os.getenv("GEMINI_LIVE_MODEL",   "gemini-2.0-flash-live-001")


def _is_mock() -> bool:
    return os.getenv("USE_MOCK_GCP", "true").lower() == "true"


@lru_cache(maxsize=1)
def _build_client():
    """Singleton Gemini client — built once, reused everywhere."""
    api_key    = os.getenv("GEMINI_API_KEY", "")
    use_vertex = os.getenv("USE_VERTEX_AI", "false").lower() == "true"

    if api_key:
        from google import genai
        print(f"[Gemini] Using Google AI Studio — Flash: {FLASH_MODEL} | Pro: {PRO_MODEL}")
        return genai.Client(api_key=api_key)
    if use_vertex:
        from google import genai
        project  = os.getenv("GOOGLE_CLOUD_PROJECT")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        print(f"[Gemini] Using Vertex AI — project: {project} | Flash: {FLASH_MODEL}")
        return genai.Client(vertexai=True, project=project, location=location)
    print("[Gemini] No credentials — mock mode active")
    return None


def get_client():
    if _is_mock():
        return None
    return _build_client()


async def generate_text(prompt: str, use_pro: bool = False, json_mode: bool = False,
                        system: str = None) -> str:
    """Generate text. Runs sync SDK in thread pool to avoid blocking event loop."""
    client = get_client()
    if client is None:
        return await _mock_generate(prompt, json_mode)

    model  = PRO_MODEL if use_pro else FLASH_MODEL
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
        if "503" in err or "UNAVAILABLE" in err:
            return "Gemini AI abhi bahut busy hai — thodi der baad try karein. (Model temporarily overloaded)"
        raise


async def generate_multimodal(parts: list, use_pro: bool = True,
                               json_mode: bool = False, system: str = None) -> str:
    """Generate from multimodal input (image / audio bytes + text)."""
    client = get_client()
    if client is None:
        return json.dumps({"raw_text": "Mock OCR extracted text", "document_type": "invoice",
                           "language": "mixed", "confidence": 0.9, "key_fields": {}})

    model  = PRO_MODEL if use_pro else FLASH_MODEL
    config = {"temperature": 0.05}
    if json_mode:
        config["response_mime_type"] = "application/json"
    if system:
        config["system_instruction"] = system

    def _call():
        return client.models.generate_content(model=model, contents=parts, config=config)

    response = await asyncio.to_thread(_call)
    return response.text


async def speech_to_text(audio_bytes: bytes, language: str = None,
                          encoding: str = "MP3", mime_type: str = "audio/mp3") -> str:
    """Transcribe audio. Cloud Speech → Gemini multimodal fallback."""
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
        audio  = speech.RecognitionAudio(content=audio_bytes)
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
        print(f"[STT] Cloud Speech failed ({e}), falling back to Gemini audio")

    # Gemini multimodal fallback
    client = get_client()
    if client is None:
        return "Audio transcription unavailable"

    def _call():
        from google.genai import types
        return client.models.generate_content(
            model=STT_GEMINI_MODEL,
            contents=[
                types.Part(inline_data=types.Blob(mime_type=mime_type, data=audio_bytes)),
                types.Part(text=f"Transcribe this audio accurately. Language: {lang}. Return only the transcript text, no extra commentary."),
            ],
        )
    response = await asyncio.to_thread(_call)
    return response.text


def _parse_audio_rate(mime_type: str) -> int:
    """Extract sample rate from 'audio/L16;codec=pcm;rate=24000' style strings."""
    m = re.search(r'rate=(\d+)', mime_type or '')
    return int(m.group(1)) if m else 24000


def _pcm_to_wav(pcm: bytes, sample_rate: int = 24000) -> bytes:
    """Wrap raw PCM16 (LINEAR16) bytes in a WAV container for browser playback."""
    n = len(pcm)
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', n + 36, b'WAVE',
        b'fmt ', 16, 1, 1, sample_rate,
        sample_rate * 2, 2, 16,
        b'data', n,
    )
    return header + pcm


async def text_to_speech(text: str, language: str = None) -> bytes:
    """Synthesize speech via Gemini TTS. Returns WAV bytes, or b'' on failure."""
    if _is_mock():
        return b""

    client = get_client()
    if client is None:
        return b""

    lang = language or TTS_LANG

    def _call():
        from google.genai import types
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
        print(f"[TTS] Gemini TTS OK — {len(pcm)} bytes PCM at {rate}Hz")
        return _pcm_to_wav(pcm, rate)
    except Exception as e:
        print(f"[TTS] Gemini TTS failed: {e}")
        return b""


# ── Mock responses (only used when USE_MOCK_GCP=true) ──────────────────────
async def _mock_generate(prompt: str, json_mode: bool) -> str:
    p = prompt.lower()
    if json_mode:
        if "order" in p or "parse" in p:
            return json.dumps({"customer": "Ramesh", "items": [
                {"name": "Steel Rods", "quantity": 50, "unit": "rods", "price": 85},
            ], "delivery_date": "tomorrow", "confidence": 0.92, "notes": ""})
        if "ambig" in p or "clarif" in p:
            return json.dumps({"status": "CLEAR", "ambiguity_type": "",
                               "clarification_question": "", "confidence": 0.95})
        if "notice" in p or "demand" in p or "penalty" in p or "translate" in p:
            return json.dumps({
                "hindi_translation": "₹57,600 की मांग की गई है। 30 दिनों में भुगतान करें।",
                "notice_type": "DRC-01", "action_items": ["30 दिन में भरें", "CA से सलाह लें"],
                "deadline": "2024-03-01", "severity": "high",
                "penalty_amount": 4500, "escalation_required": False,
            })
        if "collection" in p or "reminder" in p or "due_days" in p:
            return json.dumps({
                "risk": "MEDIUM", "risk_score": 0.6,
                "message": "Namaste ji, invoice baki hai. Kripya jaldi bhugtaan karein.",
                "recommended_action": "whatsapp", "follow_up_days": 3,
            })
        if "ocr" in p or "extract" in p or "document" in p:
            return json.dumps({"raw_text": "Invoice #1234 Steel Rods 50 units @ ₹85",
                               "document_type": "invoice", "language": "mixed",
                               "confidence": 0.88, "key_fields": {"amount": "4250"}})
        if "gstr" in p or "validate" in p:
            return json.dumps({"overall_status": "valid", "issues": [],
                               "suggestions": ["HSN codes valid", "Ready to file"],
                               "filing_ready": True})
        return json.dumps({"status": "ok", "message": "Mock response"})

    return "Mock: " + (prompt[:80] if len(prompt) > 80 else prompt)
