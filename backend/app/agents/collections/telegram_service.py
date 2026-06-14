import httpx
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

async def send_telegram_message(chat_id: str, message: str) -> dict:
    """
    Returns:
      { "success": bool, "sid": str|None, "error": str|None }
    """
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not configured.")
        return {"success": False, "sid": None, "error": "No token"}

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10.0)
            data = resp.json()
            if data.get("ok"):
                return {"success": True, "sid": str(data["result"]["message_id"]), "error": None}
            else:
                err = data.get("description", "Unknown Telegram error")
                logger.error(f"Telegram send failed: {err}")
                return {"success": False, "sid": None, "error": err}
    except Exception as e:
        logger.error(f"Telegram HTTP request failed: {e}")
        return {"success": False, "sid": None, "error": str(e)}
