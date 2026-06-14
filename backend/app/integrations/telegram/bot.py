import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from app.integrations.telegram.config import get_telegram_config
from app.integrations.telegram.handlers import start_handler, help_handler, message_handler, voice_handler, button_callback_handler

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_bot_async():
    config = get_telegram_config()
    
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing. Failing fast.")
        return None

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    
    # Voice messages
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    
    # Let message handler parse simulated commands like /orders, etc. if they are typed without handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    # Also pass unknown commands to message handler (so /orders works)
    application.add_handler(MessageHandler(filters.COMMAND, message_handler))
    
    # Callback Query
    application.add_handler(CallbackQueryHandler(button_callback_handler))

    logger.info("Starting Telegram Bot (Async Background)...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling()
    return application

async def stop_bot_async(application):
    if application:
        logger.info("Stopping Telegram Bot...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

def main():
    config = get_telegram_config()
    
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing. Failing fast.")
        return

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # Commands
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    
    # Voice messages
    application.add_handler(MessageHandler(filters.VOICE, voice_handler))
    
    # Let message handler parse simulated commands like /orders, etc. if they are typed without handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    # Also pass unknown commands to message handler (so /orders works)
    application.add_handler(MessageHandler(filters.COMMAND, message_handler))
    
    # Callback Query
    application.add_handler(CallbackQueryHandler(button_callback_handler))

    logger.info("Starting Telegram Bot (Long Polling)...")
    application.run_polling()

if __name__ == "__main__":
    main()
