import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.integrations.telegram.config import get_telegram_config
from app.database.session import SessionLocal
from app.communication.schemas import CommunicationRequest
from app.services.communication_service import CommunicationService

logger = logging.getLogger(__name__)
config = get_telegram_config()

class UnauthorizedUserError(Exception):
    pass

class TelegramFormatter:
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

def is_authorized(user_id: int) -> bool:
    if not config.allowed_users:
        return True # if no whitelist, allow all for dev purposes
    return user_id in config.allowed_users

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        logger.warning(f"Unauthorized access attempt by {user_id}")
        await update.message.reply_text("Unauthorized access.")
        return
    await update.message.reply_text("Welcome to Vyapaar Saarthi Telegram Integration. How can I help you?")

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("Unauthorized access.")
        return
    help_text = (
        "Commands:\n"
        "/orders - List orders\n"
        "/pending - List pending orders\n"
        "/today - List today's deliveries\n"
        "/overdue - List overdue orders\n\n"
        "You can also just type your request naturally:\n"
        "- 'Create order for Ramesh 20 cement bags tomorrow'\n"
        "- 'ORD-123 completed'"
    )
    await update.message.reply_text(help_text)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        logger.warning(f"Unauthorized access attempt by {user_id}")
        await update.message.reply_text("Unauthorized access.")
        return

    text = update.message.text
    logger.info(f"Received message from {user_id}: {text}")

    db = SessionLocal()
    try:
        service = CommunicationService(db)
        request = CommunicationRequest(message_text=text, user_id=str(user_id))
        response = await service.process_message(request)
        
        reply_text = TelegramFormatter.format_response(response)
        await update.message.reply_text(reply_text, parse_mode="Markdown")
        logger.info(f"Response sent to {user_id}")
    except Exception as e:
        logger.error(f"CommunicationError: {str(e)}")
        await update.message.reply_text("An error occurred while processing your request.")
    finally:
        db.close()

async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        logger.warning(f"Unauthorized access attempt by {user_id}")
        await update.message.reply_text("Unauthorized access.")
        return

    logger.info(f"Received voice message from {user_id}")
    
    try:
        voice_file = await update.message.voice.get_file()
        file_byte_array = await voice_file.download_as_bytearray()
        
        # Send a thinking indicator
        msg = await update.message.reply_text("🎤 Sun rahi hoon... (Listening...)")
        
        from app.core.gemini_client import speech_to_text
        # Telegram voice notes are usually OGG Opus
        transcription = await speech_to_text(bytes(file_byte_array), mime_type="audio/ogg")
        
        logger.info(f"Transcribed voice from {user_id}: {transcription}")
        
        # Update the processing message
        await msg.edit_text(f"📝 *Aapne kaha:*\n_{transcription}_\n\n🔄 Processing...", parse_mode="Markdown")
        
        db = SessionLocal()
        try:
            service = CommunicationService(db)
            request = CommunicationRequest(message_text=transcription, user_id=str(user_id))
            response = await service.process_message(request)
            
            reply_text = TelegramFormatter.format_response(response)
            await msg.edit_text(f"📝 *Aapne kaha:*\n_{transcription}_\n\n{reply_text}", parse_mode="Markdown")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Voice handling error: {str(e)}")
        await update.message.reply_text("Sorry, there was an error processing your voice message.")
