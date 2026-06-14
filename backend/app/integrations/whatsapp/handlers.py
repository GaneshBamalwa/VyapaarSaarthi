import logging
from app.integrations.whatsapp.config import get_whatsapp_config
from app.integrations.whatsapp.client import WhatsAppClient
from app.database.session import SessionLocal
from app.communication.schemas import CommunicationRequest
from app.services.communication_service import CommunicationService

logger = logging.getLogger(__name__)
config = get_whatsapp_config()


class UnauthorizedUserError(Exception):
    pass


class WhatsAppFormatter:
    """WhatsApp uses the same `*bold*` / `_italic_` markup as Telegram Markdown."""

    @staticmethod
    def format_response(response) -> str:
        if not response.success:
            return f"❌ {response.message}"

        if response.data and "orders" in response.data:
            orders = response.data["orders"]
            if not orders:
                return "No orders found."

            lines = [f"📊 *{response.message}*"]
            for o in orders:
                lines.append(f"• *ORD-{o['id']}* | {o['customer']} | {o['status']} | {o['date']}")
            return "\n".join(lines)

        if response.data and "order_id" in response.data:
            return f"✅ *Success*\n{response.message}"

        return f"✅ {response.message}"


HELP_TEXT = (
    "Commands:\n"
    "/orders - List orders\n"
    "/pending - List pending orders\n"
    "/today - List today's deliveries\n"
    "/overdue - List overdue orders\n\n"
    "You can also just type your request naturally:\n"
    "- 'Create order for Ramesh 20 cement bags tomorrow'\n"
    "- 'ORD-123 completed'"
)

WELCOME_TEXT = "Welcome to Vyapaar Saarthi WhatsApp Integration. How can I help you?"


def is_authorized(user_id: str) -> bool:
    if not config.allowed_users:
        return True  # if no whitelist, allow all for dev purposes
    return user_id in config.allowed_users


async def handle_text_message(client: WhatsAppClient, user_id: str, text: str) -> None:
    """Route an inbound text message, mirroring the Telegram handlers."""
    if not is_authorized(user_id):
        logger.warning(f"Unauthorized access attempt by {user_id}")
        await client.send_text(user_id, "Unauthorized access.")
        return

    stripped = text.strip()
    lowered = stripped.lower()

    # /start and /help are handled inline (WhatsApp has no native command handlers).
    if lowered in ("/start", "start", "hi", "hello", "namaste"):
        await client.send_text(user_id, WELCOME_TEXT)
        return
    if lowered in ("/help", "help"):
        await client.send_text(user_id, HELP_TEXT)
        return

    logger.info(f"Received message from {user_id}: {text}")

    db = SessionLocal()
    try:
        service = CommunicationService(db)
        request = CommunicationRequest(message_text=stripped, user_id=user_id, channel="whatsapp")
        response = await service.process_message(request)

        reply_text = WhatsAppFormatter.format_response(response)
        await client.send_text(user_id, reply_text)
        logger.info(f"Response sent to {user_id}")
    except Exception as e:
        logger.error(f"CommunicationError: {str(e)}")
        await client.send_text(user_id, "An error occurred while processing your request.")
    finally:
        db.close()


async def handle_voice_message(client: WhatsAppClient, user_id: str, media_id: str) -> None:
    """Transcribe a WhatsApp voice note and route it like a text message."""
    if not is_authorized(user_id):
        logger.warning(f"Unauthorized access attempt by {user_id}")
        await client.send_text(user_id, "Unauthorized access.")
        return

    logger.info(f"Received voice message from {user_id}")

    try:
        await client.send_text(user_id, "🎤 Sun rahi hoon... (Listening...)")

        audio_bytes = await client.download_media(media_id)

        from app.core.gemini_client import speech_to_text
        # WhatsApp voice notes are OGG Opus, same as Telegram voice notes.
        transcription = await speech_to_text(audio_bytes, mime_type="audio/ogg")
        logger.info(f"Transcribed voice from {user_id}: {transcription}")

        db = SessionLocal()
        try:
            service = CommunicationService(db)
            request = CommunicationRequest(message_text=transcription, user_id=user_id, channel="whatsapp")
            response = await service.process_message(request)

            reply_text = WhatsAppFormatter.format_response(response)
            await client.send_text(
                user_id,
                f"📝 *Aapne kaha:*\n_{transcription}_\n\n{reply_text}",
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Voice handling error: {str(e)}")
        await client.send_text(user_id, "Sorry, there was an error processing your voice message.")
