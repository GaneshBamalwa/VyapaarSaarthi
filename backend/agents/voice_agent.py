"""
Voice & Chat Pipeline
- Understands Hinglish / Hindi queries
- Writes to DB: creates orders, logs notices, triggers agent pipelines
- Generates TTS audio responses via Cloud TTS (Gemini fallback)
"""
import os
import json
import uuid
from datetime import datetime
from typing import Optional
from utils import gemini_client as _gc
from utils.ws_manager import ws_manager

STATIC_DIR = os.path.join(os.path.dirname(__file__), "../static/audio")
os.makedirs(STATIC_DIR, exist_ok=True)

INTENT_ROUTING = {
    "order":       ["order", "chahiye", "bhejo", "delivery", "kharido", "units", "kg", "pieces", "send", "mangao", "book"],
    "invoice":     ["invoice", "bill", "payment", "bhugtan", "receipt", "due", "pending"],
    "cash_flow":   ["cash flow", "paisa", "income", "expense", "projection", "forecast", "revenue", "kamai"],
    "gst":         ["gst", "tax", "return", "filing", "notice", "challan", "asmt", "drc"],
    "collections": ["overdue", "late", "reminder", "recover", "baaki", "outstanding"],
    "schemes":     ["scheme", "loan", "mudra", "government", "yojana", "eligible", "subsidy"],
    "general":     [],
}

SYSTEM_PROMPT = """You are VyapaarOS, an intelligent AI business assistant for Indian MSME owners.
You understand Hinglish (Hindi-English mixed) and always respond in the same language as the user.
You have real-time access to the seller's business data: orders, invoices, buyers, GST records, and compliance status.

When users ask about orders, collections, GST, or invoices — use the live business context provided.
Be concise, friendly, and action-oriented. Use ₹ for currency. Keep responses under 120 words.
Always confirm any action you take (e.g., "Order create kar diya hai Ramesh ke liye")."""


def detect_intent(text: str) -> str:
    text_lower = text.lower()
    for intent, keywords in INTENT_ROUTING.items():
        if any(kw in text_lower for kw in keywords):
            return intent
    return "general"


async def process_chat_message(
    message: str,
    session_id: str,
    conversation_history: list,
    db_context: Optional[dict] = None,
) -> dict:
    await ws_manager.broadcast_agent("Voice Agent", "thinking",
        f"Processing: '{message[:60]}...'" if len(message) > 60 else f"Processing: '{message}'")

    intent = detect_intent(message)
    await ws_manager.broadcast_agent("Voice Agent", "decision", f"Intent detected: {intent}")

    context_str = ""
    if db_context:
        context_str = f"\n\nLive business context (use this for accurate answers):\n{json.dumps(db_context, indent=2, ensure_ascii=False)}"

    history_str = ""
    if conversation_history:
        recent = conversation_history[-4:]
        history_str = "\n".join([f"{m['role'].title()}: {m['content']}" for m in recent])
        history_str = f"\n\nConversation history:\n{history_str}"

    prompt = f"""{SYSTEM_PROMPT}
{context_str}
{history_str}

User ({intent} intent): {message}

Respond helpfully based on the live business context. If the user is placing an order, confirm you will create it. Be specific with names and numbers from the context."""

    response_text = await _gc.generate_text(prompt)
    await ws_manager.broadcast_agent("Voice Agent", "completed",
        f"Response generated for intent: {intent}")

    return {
        "session_id": session_id,
        "user_message": message,
        "response": response_text,
        "intent": intent,
        "timestamp": datetime.utcnow().isoformat(),
    }


async def transcribe_audio(audio_bytes: bytes, language: str = "hi-IN") -> str:
    await ws_manager.broadcast_agent("Voice Agent", "thinking", "Transcribing audio...")
    transcript = await _gc.speech_to_text(audio_bytes, language)
    await ws_manager.broadcast_agent("Voice Agent", "completed", f"Transcribed: '{transcript[:80]}'")
    return transcript


async def synthesize_speech(text: str, language: str = "hi-IN") -> str | None:
    """Returns a URL path to the generated audio file, or None if TTS unavailable."""
    await ws_manager.broadcast_agent("Voice Agent", "thinking", "Generating audio response...")
    audio_bytes = await _gc.text_to_speech(text, language)

    # Silence placeholder returned when TTS isn't configured — don't save it
    if not audio_bytes or len(audio_bytes) < 100:
        await ws_manager.broadcast_agent("Voice Agent", "completed", "Audio unavailable (TTS not configured)")
        return None

    filename = f"response_{uuid.uuid4().hex[:8]}.wav"
    filepath = os.path.join(STATIC_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(audio_bytes)

    await ws_manager.broadcast_agent("Voice Agent", "completed", "Audio response ready")
    return f"/static/audio/{filename}"


async def generate_weekly_briefing(business_data: dict) -> dict:
    """Generates a Hindi audio briefing of weekly business performance."""
    await ws_manager.broadcast_agent("Voice Agent", "thinking", "Generating weekly Hindi briefing...")

    prompt = f"""Create a 90-second spoken Hindi business briefing for an MSME owner.
Real business data: {json.dumps(business_data, ensure_ascii=False)}
Cover: weekly revenue, outstanding collections with amounts, top buyer, GST filing deadlines.
Write in warm conversational Hindi. Be specific with numbers. Max 120 words."""

    script = await _gc.generate_text(prompt)
    audio_url = await synthesize_speech(script, "hi-IN")

    return {
        "script": script,
        "audio_url": audio_url,
        "duration_seconds": 90,
        "generated_at": datetime.utcnow().isoformat(),
    }
