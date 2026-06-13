"""
Clarification Agent — detects ambiguous/vague orders before intake processing.
Triggers HITL if the order is too unclear to auto-process.
"""
import json
import time
from utils.gemini_client import generate_text
from utils.ws_manager import ws_manager

SYSTEM_PROMPT = """You are an intelligent order clarification assistant for Indian MSMEs.
Your job is to detect if an order request is ambiguous, incomplete, or unclear.

Rules:
1. If the order is clear and complete → status: "CLEAR"
2. If the order is ambiguous or missing key info → status: "AMBIGUOUS"
3. Generate a natural Hindi clarification question if ambiguous.
4. Look for: missing item names, missing quantities, vague references ("wahi maal", "same as before").
5. Always respond with valid JSON only.

Output format:
{
  "status": "CLEAR" or "AMBIGUOUS",
  "ambiguity_type": "missing_item|missing_quantity|vague_reference|missing_customer|other",
  "clarification_question": "Hindi question if ambiguous, empty string if clear",
  "confidence": 0.0 to 1.0
}"""

USER_TEMPLATE = "Check this order for ambiguity: {text}"


async def run(text: str, order_id: int = None) -> dict:
    await ws_manager.emit_agent_event("ClarificationAgent", "running", "checking_ambiguity", order_id=order_id)
    start = time.time()
    try:
        raw = await generate_text(
            USER_TEMPLATE.format(text=text),
            use_pro=False,
            json_mode=True,
            system=SYSTEM_PROMPT,
        )
        data = json.loads(raw.strip())
        duration_ms = int((time.time() - start) * 1000)
        event = "order_ambiguous" if data.get("status") == "AMBIGUOUS" else "order_clear"
        await ws_manager.emit_agent_event("ClarificationAgent", "completed", event,
                                          data=data, order_id=order_id)
        return {"status": "success", "agent": "ClarificationAgent", "data": data, "duration_ms": duration_ms}
    except Exception as e:
        await ws_manager.emit_agent_event("ClarificationAgent", "failed", "agent_error", error=str(e))
        return {"status": "error", "agent": "ClarificationAgent", "error": str(e)}
