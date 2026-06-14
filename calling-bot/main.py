"""Vyapaar Saarthi — Mobile Calling Bot (Twilio Voice).

Flow (mirrors the Telegram voice handler, but over a phone call):
  1. Caller dials the Twilio number  -> Twilio POSTs /voice/incoming
  2. We greet and open a <Gather input="speech"> so Twilio transcribes the caller
  3. Twilio POSTs the transcript to /voice/process
  4. We forward the text to the backend's shared CommunicationService
     (POST /api/communication/message) — the exact same pipeline Telegram uses
  5. We speak the reply back and listen again, until the caller says goodbye.

Twilio's built-in speech recognition handles the audio->text step, so no audio
download/transcription plumbing is needed here.
"""

import os
import logging

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.request_validator import RequestValidator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("calling-bot")

# ── Config ────────────────────────────────────────────────────────────────────
PORT = int(os.getenv("PORT", "8002"))
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
COMM_ENDPOINT = f"{BACKEND_URL}/api/communication/message"
VOICE_LANGUAGE = os.getenv("VOICE_LANGUAGE", "hi-IN")
SPEECH_TIMEOUT = os.getenv("SPEECH_TIMEOUT", "auto")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
# Public HTTPS base URL (e.g. ngrok) used to verify Twilio's signature. When the
# app runs behind a proxy, request.url is the internal URL, so Twilio's signature
# won't match unless we reconstruct the public URL it actually signed.
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")

GREETING = os.getenv(
    "VOICE_GREETING",
    "Namaste! Vyapaar Saarthi mein aapka swagat hai. "
    "Boliye, main aapki kya madad kar sakti hoon?",
)
GOODBYE = "Dhanyavaad! Vyapaar Saarthi ko call karne ke liye shukriya."
ERROR_MSG = "Maaf kijiye, abhi koi takneeki samasya aa gayi hai. Kripya baad mein try karein."
NO_INPUT_MSG = "Mujhe kuch sunai nahi diya. Kripya phir se boliye."
FOLLOW_UP = "Kuch aur poochhna hai?"

# Words that end the call.
GOODBYE_WORDS = ("bye", "goodbye", "dhanyavaad", "dhanyawad", "shukriya", "bas", "nahi", "nahin", "no", "stop")

app = FastAPI(title="Vyapaar Saarthi Calling Bot")
_validator = RequestValidator(TWILIO_AUTH_TOKEN) if TWILIO_AUTH_TOKEN else None


# ── Helpers ───────────────────────────────────────────────────────────────────
def _xml(vr: VoiceResponse) -> Response:
    return Response(content=str(vr), media_type="application/xml")


def _gather(prompt: str) -> Gather:
    """A speech Gather that posts the transcript to /voice/process."""
    gather = Gather(
        input="speech",
        action="/voice/process",
        method="POST",
        language=VOICE_LANGUAGE,
        speech_timeout=SPEECH_TIMEOUT,
    )
    gather.say(prompt, language=VOICE_LANGUAGE)
    return gather


def _is_goodbye(text: str) -> bool:
    t = text.lower().strip()
    return t in GOODBYE_WORDS or any(t == w for w in GOODBYE_WORDS)


def _validate(request: Request, form: dict) -> bool:
    if _validator is None:
        return True
    signature = request.headers.get("X-Twilio-Signature", "")
    url = (PUBLIC_BASE_URL + request.url.path) if PUBLIC_BASE_URL else str(request.url)
    return _validator.validate(url, form, signature)


def _spoken_reply(payload: dict) -> str:
    """Turn a CommunicationResponse into plain text suitable for <Say>."""
    message = payload.get("message") or "Theek hai."
    data = payload.get("data") or {}
    orders = data.get("orders")
    if isinstance(orders, list) and orders:
        lines = [message]
        for o in orders[:5]:
            lines.append(f"Order {o.get('id')}, {o.get('customer')}, status {o.get('status')}.")
        return " ".join(lines)
    return message


async def _ask_backend(text: str, caller: str) -> str:
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            COMM_ENDPOINT,
            json={"message_text": text, "user_id": caller, "channel": "voice"},
        )
        resp.raise_for_status()
        return _spoken_reply(resp.json())


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "backend": COMM_ENDPOINT}


@app.post("/voice/incoming")
async def voice_incoming(request: Request):
    """Entry point Twilio hits when a call connects."""
    form = dict(await request.form())
    if not _validate(request, form):
        return Response(content="Invalid Twilio signature", status_code=403)

    vr = VoiceResponse()
    vr.append(_gather(GREETING))
    # Reached only if the caller said nothing during the Gather.
    vr.say(GOODBYE, language=VOICE_LANGUAGE)
    vr.hangup()
    return _xml(vr)


@app.post("/voice/process")
async def voice_process(request: Request):
    """Handles each transcribed utterance and continues the conversation."""
    form = dict(await request.form())
    if not _validate(request, form):
        return Response(content="Invalid Twilio signature", status_code=403)

    speech = (form.get("SpeechResult") or "").strip()
    caller = form.get("From") or "unknown"
    logger.info("Caller %s said: %s", caller, speech)

    vr = VoiceResponse()

    if not speech:
        vr.append(_gather(NO_INPUT_MSG))
        vr.say(GOODBYE, language=VOICE_LANGUAGE)
        vr.hangup()
        return _xml(vr)

    if _is_goodbye(speech):
        vr.say(GOODBYE, language=VOICE_LANGUAGE)
        vr.hangup()
        return _xml(vr)

    try:
        reply = await _ask_backend(speech, caller)
    except Exception as e:
        logger.error("Backend call failed: %s", e)
        vr.say(ERROR_MSG, language=VOICE_LANGUAGE)
        vr.hangup()
        return _xml(vr)

    logger.info("Replying to %s: %s", caller, reply)
    # Speak the answer, then listen for the next command.
    vr.append(_gather(f"{reply} {FOLLOW_UP}"))
    vr.say(GOODBYE, language=VOICE_LANGUAGE)
    vr.hangup()
    return _xml(vr)


if __name__ == "__main__":
    import uvicorn

    logger.info("📞 Calling bot running on http://localhost:%s (backend: %s)", PORT, BACKEND_URL)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
