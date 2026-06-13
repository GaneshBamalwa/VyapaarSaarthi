"""
Collections Agent — assesses overdue invoice risk and generates Hindi payment reminders.
Risk tiers: LOW (1-7d) → friendly | MEDIUM (8-20d) → firm | HIGH (21+d) → urgent/legal
"""
import json
import time
from utils.gemini_client import generate_text
from utils.ws_manager import ws_manager

SYSTEM_PROMPT = """You are an intelligent collections assistant for Indian MSMEs.
Your job is to assess overdue invoice risk and generate appropriate Hindi payment reminders.

Risk Assessment Rules:
- LOW: 1-7 days overdue → Gentle, polite Hindi reminder
- MEDIUM: 8-20 days overdue → Firm, professional Hindi reminder
- HIGH: 21+ days overdue → Urgent, serious Hindi reminder with legal warning

Always respond with valid JSON only.

Output format:
{
  "risk": "LOW" or "MEDIUM" or "HIGH",
  "risk_score": 0.0 to 1.0,
  "message": "Hindi reminder message with customer name and amount",
  "recommended_action": "call|whatsapp|legal_notice",
  "follow_up_days": number
}"""

USER_TEMPLATE = """Generate collection reminder for:
Invoice ID: {invoice_id}
Customer: {customer}
Amount: ₹{amount}
Days Overdue: {due_days}
Previous Reminders Sent: {previous_reminders}"""


async def run(invoice_id: str, customer: str, amount: float,
              due_days: int, previous_reminders: int = 0) -> dict:
    await ws_manager.emit_agent_event("CollectionsAgent", "running", "analyzing_invoice",
                                      data={"invoice_id": invoice_id})
    start = time.time()
    try:
        raw = await generate_text(
            USER_TEMPLATE.format(invoice_id=invoice_id, customer=customer,
                                 amount=amount, due_days=due_days,
                                 previous_reminders=previous_reminders),
            use_pro=False,
            json_mode=True,
            system=SYSTEM_PROMPT,
        )
        data = json.loads(raw.strip())
        duration_ms = int((time.time() - start) * 1000)
        await ws_manager.emit_agent_event(
            "CollectionsAgent", "completed", "reminder_generated",
            data={"risk": data.get("risk"), "invoice_id": invoice_id},
        )
        return {"status": "success", "agent": "CollectionsAgent", "data": data, "duration_ms": duration_ms}
    except Exception as e:
        await ws_manager.emit_agent_event("CollectionsAgent", "failed", "agent_error", error=str(e))
        return {"status": "error", "agent": "CollectionsAgent", "error": str(e)}
