"""
Order Intake Agent — parses unstructured Hinglish/Hindi order text into structured JSON.
Uses Gemini Flash for fast, cheap inference.
"""
import json
import time
from utils.gemini_client import generate_text
from utils.ws_manager import ws_manager

SYSTEM_PROMPT = """You are an intelligent order intake assistant for Indian MSMEs.
Your job is to parse unstructured Hindi/English order requests into structured JSON.

Rules:
1. Extract customer name if mentioned (often "bhai", "bhaiya", or a proper name).
2. Extract all items with their quantities and units.
3. Extract delivery date (convert relative dates: "kal" = tomorrow, "Friday" = next Friday).
4. If customer name is unclear, leave it as empty string.
5. Always respond with valid JSON only, no explanations.
6. Quantities should be integers.
7. Common units: bags, rods, boxes, pieces, kg, litre, meter, dozen.

Output format:
{
  "customer": "name or empty string",
  "items": [{"name": "item name", "quantity": 20, "unit": "bags"}],
  "delivery_date": "YYYY-MM-DD or relative description",
  "confidence": 0.0 to 1.0,
  "notes": "any additional context"
}"""

USER_TEMPLATE = "Parse this order: {text}"


async def run(text: str, order_id: int = None) -> dict:
    await ws_manager.emit_agent_event("IntakeAgent", "running", "parsing_order", order_id=order_id)
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
        await ws_manager.emit_agent_event(
            "IntakeAgent", "completed", "order_parsed",
            data={"customer": data.get("customer"), "confidence": data.get("confidence")},
            order_id=order_id,
        )
        return {"status": "success", "agent": "IntakeAgent", "data": data, "duration_ms": duration_ms}
    except Exception as e:
        await ws_manager.emit_agent_event("IntakeAgent", "failed", "parse_error", error=str(e), order_id=order_id)
        return {"status": "error", "agent": "IntakeAgent", "error": str(e)}
