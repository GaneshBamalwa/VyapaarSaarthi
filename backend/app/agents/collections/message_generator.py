import asyncio
from app.core.gemini_client import get_gemini_client
from app.core.config import get_settings
from app.core.logging import get_logger
from app.agents.collections.risk_engine import format_inr

settings = get_settings()
logger = get_logger(__name__)

FALLBACK_LEVEL_1 = """नमस्ते {buyer_name} जी,

उम्मीद है सब ठीक होगा। Invoice #{invoice_id} का ₹{amount} का भुगतान \
{days_overdue} दिन से due है।

कृपया जल्द भुगतान कर दें।

धन्यवाद,
{business_name}"""

FALLBACK_LEVEL_2 = """{buyer_name} जी,

आपका Invoice #{invoice_id} का ₹{amount} का भुगतान {days_overdue} दिनों \
से लंबित है।

कृपया आज ही भुगतान करें। देरी होने पर supply रोकनी पड़ सकती है।

— {business_name}"""


async def generate_reminder_message(
    buyer_name: str,
    invoice_id: int,
    amount: float,
    days_overdue: int,
    level: int,
    business_name: str,
    past_late_count: int = 0,
) -> str:
    """
    Generates a clear, deterministic WhatsApp reminder without relying on the LLM.
    Ensures no truncation bugs occur.
    """
    amount_str = f"₹{format_inr(amount)}"
    
    if level == 1:
        return (
            f"Hello {buyer_name},\n\n"
            f"This is a gentle reminder from {business_name}.\n"
            f"Your payment of *{amount_str}* for Order #{invoice_id} is currently {days_overdue} days overdue.\n\n"
            f"Please arrange the payment at your earliest convenience."
        )
    else:
        return (
            f"URGENT: {buyer_name},\n\n"
            f"Your payment of *{amount_str}* for Order #{invoice_id} is {days_overdue} days overdue.\n\n"
            f"Please clear this immediately to avoid any interruption in future supply.\n\n"
            f"- {business_name}"
        )


