from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


def format_phone_for_whatsapp(phone: str) -> str:
    """
    Ensures phone is in format: whatsapp:+91XXXXXXXXXX
    - Strips spaces, dashes, brackets
    - If starts with 0, replace with +91
    - If 10 digits with no country code, prepend +91
    - If already has +91, keep it
    - Prepend whatsapp: prefix
    """
    # Remove whatsapp: prefix if already present (we'll re-add it)
    cleaned = phone.strip()
    if cleaned.startswith("whatsapp:"):
        cleaned = cleaned[len("whatsapp:"):]

    # Strip non-digit characters except leading +
    has_plus = cleaned.startswith("+")
    digits_only = "".join(c for c in cleaned if c.isdigit())

    if has_plus:
        number = "+" + digits_only
    elif digits_only.startswith("0"):
        number = "+91" + digits_only[1:]
    elif len(digits_only) == 10:
        number = "+91" + digits_only
    else:
        number = "+" + digits_only  # best-effort

    return f"whatsapp:{number}"


async def send_whatsapp_message(to_phone: str, message: str) -> dict:
    """
    Returns:
      { "success": bool, "sid": str|None, "error": str|None }
    Never raises — always returns the dict.
    """
    if not settings.WHATSAPP_ENABLED:
        logger.info(f"[WhatsApp DEV MODE] To: {to_phone}")
        logger.info(f"[WhatsApp DEV MODE] Message:\n{message}")
        return {"success": True, "sid": "dev-no-send", "error": None}

    try:
        from twilio.rest import Client  # lazy import — optional dependency

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        formatted = format_phone_for_whatsapp(to_phone)
        msg = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=formatted,
            body=message,
        )
        return {"success": True, "sid": msg.sid, "error": None}
    except Exception as e:
        logger.error(f"Twilio send failed: {e}")
        return {"success": False, "sid": None, "error": str(e)}
