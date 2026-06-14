import logging
from fastapi import APIRouter, Request, Response, Query
from app.integrations.whatsapp.config import get_whatsapp_config
from app.integrations.whatsapp.client import WhatsAppClient
from app.integrations.whatsapp.handlers import handle_text_message, handle_voice_message

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp Integration"])

config = get_whatsapp_config()


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Webhook verification handshake required by Meta when subscribing."""
    if hub_mode == "subscribe" and hub_verify_token == config.WHATSAPP_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified.")
        return Response(content=hub_challenge or "", media_type="text/plain")
    logger.warning("WhatsApp webhook verification failed.")
    return Response(content="Verification failed", status_code=403)


@router.post("/webhook")
async def receive_webhook(request: Request):
    """Receive inbound WhatsApp messages (text + voice) from the Cloud API."""
    payload = await request.json()
    logger.info(f"WhatsApp webhook payload: {payload}")

    client = WhatsAppClient()

    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])
                for message in messages:
                    sender = message.get("from")
                    msg_type = message.get("type")

                    if msg_type == "text":
                        text = message.get("text", {}).get("body", "")
                        await handle_text_message(client, sender, text)
                    elif msg_type in ("audio", "voice"):
                        media_id = message.get(msg_type, {}).get("id")
                        if media_id:
                            await handle_voice_message(client, sender, media_id)
                    else:
                        await client.send_text(
                            sender,
                            "Sorry, I can only handle text and voice messages right now.",
                        )
    except Exception as e:
        logger.error(f"Error handling WhatsApp webhook: {str(e)}")

    # Always 200 so Meta does not retry/disable the webhook.
    return {"status": "ok"}
