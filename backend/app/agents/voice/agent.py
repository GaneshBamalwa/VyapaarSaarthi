import os
import uuid
import json
from datetime import datetime
from typing import Any, Optional
from app.agents.base import BaseAgent
from app.core import gemini_client as _gc
from app.core.config import get_settings

settings = get_settings()
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../static/audio"))


class VoiceAgent(BaseAgent):
    name = "Voice Agent"

    INTENT_ROUTING = {
        "order":       ["order", "chahiye", "bhejo", "delivery", "kharido", "units", "kg", "pieces", "send", "mangao", "book", "ऑर्डर", "चाहिए", "भेजो", "डिलीवरी", "खरीदो", "किलो", "पीस", "मंगाओ", "बुक"],
        "invoice":     ["invoice", "bill", "payment", "bhugtan", "receipt", "due", "pending", "इनवॉइस", "बिल", "पेमेंट", "भुगतान", "रसीद"],
        "cash_flow":   ["cash flow", "paisa", "income", "expense", "projection", "forecast", "revenue", "kamai", "कैश फ्लो", "पैसा", "इनकम", "खर्च", "कमाई"],
        "gst":         ["gst", "tax", "return", "filing", "notice", "challan", "asmt", "drc", "टैक्स", "रिटर्न", "फाइलिंग", "नोटिस", "चालान"],
        "collections": ["overdue", "late", "reminder", "recover", "baaki", "outstanding", "लेट", "रिमाइंडर", "रिकवर", "बाकी"],
        "schemes":     ["scheme", "loan", "mudra", "government", "yojana", "eligible", "subsidy", "स्कीम", "लोन", "मुद्रा", "योजना", "सब्सिडी"],
        "fulfill":     ["fulfill", "complete", "done", "pura", "khatam", "mark", "ho gaya", "पूरा", "खत्म", "हो गया"],
        "general":     [],
    }

    SYSTEM_PROMPT = """You are VyapaarOS, an intelligent female AI business assistant for Indian MSME owners.
You understand Hinglish (Hindi-English mixed) and always respond in the same language as the user.
Always use female pronouns for yourself (e.g. "Main kar rahi hoon", "Maine order place kar di hai").
You have real-time access to the seller's business data: orders, invoices, buyers, GST records, and compliance status.

When users ask about orders, collections, GST, or invoices — use the live business context provided.
Be concise, friendly, and action-oriented. Use ₹ for currency. Keep responses under 120 words.
Always confirm any action you take (e.g., "Order create kar di hai Ramesh ke liye")."""

    def __init__(self):
        super().__init__()
        os.makedirs(STATIC_DIR, exist_ok=True)

    def detect_intent(self, text: str) -> str:
        text_lower = text.lower()
        for intent, keywords in self.INTENT_ROUTING.items():
            if any(kw in text_lower for kw in keywords):
                return intent
        return "general"

    async def invoke(self, input_data: dict, **kwargs) -> dict[str, Any]:
        action = input_data.get("action", "chat")
        try:
            if action == "chat":
                import datetime
                current_time = datetime.datetime.now().strftime("%A, %Y-%m-%d %I:%M %p")
                
                # We inject time into db_context for the standard agent
                db_context = input_data.get("db_context", "")
                dynamic_context = f"{db_context}\n\n[SYSTEM CLOCK: The current date and time is {current_time}]"

                res = await self.chat(
                    message=input_data.get("message", ""),
                    session_id=input_data.get("session_id") or str(uuid.uuid4()),
                    conversation_history=input_data.get("conversation_history", []),
                    db_context=dynamic_context,
                )
                return self._success(res)
            elif action == "transcribe":
                res = await self.transcribe(
                    audio_bytes=input_data.get("audio_bytes", b""),
                    language=input_data.get("language", "hi-IN"),
                )
                return self._success({"transcript": res})
            elif action == "synthesize":
                res = await self.synthesize(
                    text=input_data.get("text", ""),
                    language=input_data.get("language", "hi-IN"),
                )
                return self._success({"audio_url": res})
            elif action == "weekly_briefing":
                res = await self.weekly_briefing(
                    business_data=input_data.get("business_data", {}),
                )
                return self._success(res)
            return self._failure(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"VoiceAgent execution failed: {e}")
            return self._failure(str(e))

    async def chat(
        self,
        message: str,
        session_id: str,
        conversation_history: list,
        db_context: Optional[dict] = None,
    ) -> dict:
        await self._emit("running", "processing_chat_message", data={"message": message})

        intent = self.detect_intent(message)
        await self._emit("running", "intent_detected", data={"intent": intent})

        context_str = ""
        if db_context:
            context_str = f"\n\nLive business context (use this for accurate answers):\n{json.dumps(db_context, indent=2, ensure_ascii=False)}"

        history_str = ""
        if conversation_history:
            recent = conversation_history[-4:]
            history_str = "\n".join([f"{m['role'].title()}: {m['content']}" for m in recent])
            history_str = f"\n\nConversation history:\n{history_str}"

        prompt = f"""{self.SYSTEM_PROMPT}
{context_str}
{history_str}

User ({intent} intent): {message}

Respond helpfully based on the live business context. If the user is placing an order, confirm you will create it. Be specific with names and numbers from the context."""

        response_text = await _gc.generate_text(prompt)
        await self._emit("completed", "response_generated", data={"intent": intent})

        return {
            "session_id": session_id,
            "user_message": message,
            "response": response_text,
            "intent": intent,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def transcribe(self, audio_bytes: bytes, language: str = "hi-IN") -> str:
        await self._emit("running", "transcribing_audio")
        transcript = await _gc.speech_to_text(audio_bytes, language)
        await self._emit("completed", "audio_transcribed", data={"transcript": transcript[:40] + "..."})
        return transcript

    async def synthesize(self, text: str, language: str = "hi-IN") -> Optional[str]:
        await self._emit("running", "synthesizing_speech")
        audio_bytes = await _gc.text_to_speech(text, language)

        if not audio_bytes or len(audio_bytes) < 100:
            await self._emit("completed", "speech_unavailable")
            return None

        filename = f"response_{uuid.uuid4().hex[:8]}.wav"
        filepath = os.path.join(STATIC_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(audio_bytes)

        await self._emit("completed", "speech_synthesized", data={"filename": filename})
        return f"/static/audio/{filename}"

    async def weekly_briefing(self, business_data: dict) -> dict:
        await self._emit("running", "generating_weekly_briefing")

        prompt = f"""Create a 90-second spoken Hindi business briefing for an MSME owner.
Real business data: {json.dumps(business_data, ensure_ascii=False)}
Cover: weekly revenue, outstanding collections with amounts, top buyer, GST filing deadlines.
Write in warm conversational Hindi. Be specific with numbers. Max 120 words."""

        script = await _gc.generate_text(prompt)
        audio_url = await self.synthesize(script, "hi-IN")

        await self._emit("completed", "weekly_briefing_ready")
        return {
            "script": script,
            "audio_url": audio_url,
            "duration_seconds": 90,
            "generated_at": datetime.utcnow().isoformat(),
        }
