import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from datetime import datetime
from app.integrations.telegram.config import get_telegram_config
from app.database.session import SessionLocal
from app.communication.schemas import CommunicationRequest
from app.services.communication_service import CommunicationService
from app.models.order import Order
from app.models.company import CompanyProfile
from app.services.pdf_service import PDFInvoiceService

import re

logger = logging.getLogger(__name__)
config = get_telegram_config()

USER_STATE = {}

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
        "/overdue - List overdue orders\n"
        "/invoice - Generate an invoice\n"
        "/excel - Download expenses/orders excel sheet\n\n"
        "You can also just type your request naturally:\n"
        "- 'Create order for Ramesh 20 cement bags tomorrow'\n"
        "- 'mujhe invoice chahiye'\n"
        "- 'download orders excel sheet'\n"
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
    
    # Fast path for greetings and introductions
    greet_text = text.lower().strip()
    if greet_text in ["hello", "hi", "hey", "who are you", "who are you?", "kaun ho tum"]:
        intro = (
            "👋 *Hello! I am Vyapaar Saarthi* 🤖\n\n"
            "I am your AI-powered MSME Business Operating System.\n"
            "I can help you manage your daily operations effortlessly. Just tell me what you need!\n\n"
            "📦 *Orders:* 'Create an order for Ramesh for 20 cement bags tomorrow'\n"
            "🗣️ *Voice:* You can also just send me a voice note!\n"
            "💰 *Collections:* I automatically track your overdue payments.\n\n"
            "Type /help to see all available commands."
        )
        await update.message.reply_text(intro, parse_mode="Markdown")
        return

    # Check if user is in invoice selection state
    if USER_STATE.get(user_id) == "AWAITING_INVOICE":
        if await _try_handle_invoice_selection(greet_text, update, context, user_id):
            return

    db = SessionLocal()
    try:
        service = CommunicationService(db)
        request = CommunicationRequest(message_text=text, user_id=str(user_id))
        response = await service.process_message(request)
        
        if response.data:
            if response.data.get("excel_bytes"):
                rt = response.data.get("report_type", "report")
                tm = response.data.get("target_month", "latest")
                year, month_str = tm.split("-") if "-" in tm else (tm, "")
                filename = f"{rt}_{year}_{month_str}_vyapaarsaarthi.xlsx"
                await context.bot.send_document(
                    chat_id=update.message.chat_id,
                    document=response.data["excel_bytes"],
                    filename=filename,
                    caption=response.message
                )
                return
            elif response.data.get("invoice_order_id"):
                await _send_invoice_pdf(response.data["invoice_order_id"], update.message, context)
                return
            elif response.data.get("needs_invoice_selection"):
                USER_STATE[user_id] = "AWAITING_INVOICE"
                keyboard = []
                for o in response.data["orders"]:
                    keyboard.append([InlineKeyboardButton(f"ORD-{o['id']} - {o['customer']} ({o['date']})", callback_data=f"invoice_{o['id']}")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(response.message, reply_markup=reply_markup)
                return
        
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
        greet_text = transcription.lower().strip()

        # Check if user is in invoice selection state
        if USER_STATE.get(user_id) == "AWAITING_INVOICE":
            if await _try_handle_invoice_selection(greet_text, msg, context, user_id):
                return
            
        # Update the processing message
        await msg.edit_text(f"📝 *Aapne kaha:*\n_{transcription}_\n\n🔄 Processing...", parse_mode="Markdown")
        
        db = SessionLocal()
        try:
            service = CommunicationService(db)
            request = CommunicationRequest(message_text=transcription, user_id=str(user_id))
            response = await service.process_message(request)
            
            if response.data:
                if response.data.get("excel_bytes"):
                    rt = response.data.get("report_type", "report")
                    tm = response.data.get("target_month", "latest")
                    year, month_str = tm.split("-") if "-" in tm else (tm, "")
                    filename = f"{rt}_{year}_{month_str}_vyapaarsaarthi.xlsx"
                    await context.bot.send_document(
                        chat_id=msg.chat_id,
                        document=response.data["excel_bytes"],
                        filename=filename,
                        caption=response.message
                    )
                    return
                elif response.data.get("invoice_order_id"):
                    await _send_invoice_pdf(response.data["invoice_order_id"], msg, context)
                    return
                elif response.data.get("needs_invoice_selection"):
                    USER_STATE[user_id] = "AWAITING_INVOICE"
                    keyboard = []
                    for o in response.data["orders"]:
                        keyboard.append([InlineKeyboardButton(f"ORD-{o['id']} - {o['customer']} ({o['date']})", callback_data=f"invoice_{o['id']}")])
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await msg.edit_text(response.message, reply_markup=reply_markup)
                    return
            
            reply_text = TelegramFormatter.format_response(response)
            await msg.edit_text(f"📝 *Aapne kaha:*\n_{transcription}_\n\n{reply_text}", parse_mode="Markdown")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Voice handling error: {str(e)}")
        await update.message.reply_text("Sorry, there was an error processing your voice message.")

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("invoice_"):
        order_id = int(data.split("_")[1])
        db = SessionLocal()
        try:
            order = db.query(Order).filter(Order.id == order_id).first()
            if not order:
                await query.edit_message_text("Order not found.")
                return
                
            company = db.query(CompanyProfile).first()
            if not company:
                company = CompanyProfile(company_name="Vyapaar Saarthi Default")
                
            await query.edit_message_text("Generating your invoice PDF...")
            
            pdf_bytes = PDFInvoiceService.generate_invoice(order, company)
            
            # Send Document
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=pdf_bytes,
                filename=f"Invoice_ORD-{order.id}.pdf",
                caption=f"Here is the invoice for Order #{order.id} ({order.customer})."
            )
        except Exception as e:
            logger.error(f"Invoice generation failed: {e}")
            await context.bot.send_message(chat_id=query.message.chat_id, text="Error generating invoice.")
        finally:
            db.close()

async def _try_handle_invoice_selection(text: str, message_obj, context, user_id: int) -> bool:
    match = re.search(r'(?:ord-|order\s*|number\s*)?(\d+)', text)
    db = SessionLocal()
    try:
        if match:
            order_id = int(match.group(1))
            order = db.query(Order).filter(Order.id == order_id).first()
            if order:
                USER_STATE.pop(user_id, None)
                await _send_invoice_pdf(order.id, message_obj, context)
                return True
        
        # Try matching customer name
        orders = db.query(Order).filter(Order.status.notin_(["REJECTED", "CANCELLED", "draft"])).order_by(Order.created_at.desc()).limit(20).all()
        for o in orders:
            if o.customer and o.customer.lower() in text:
                USER_STATE.pop(user_id, None)
                await _send_invoice_pdf(o.id, message_obj, context)
                return True
    finally:
        db.close()
    return False

async def _send_invoice_pdf(order_id: int, message_obj, context):
    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            await context.bot.send_message(chat_id=message_obj.chat_id, text="Order not found.")
            return
            
        company = db.query(CompanyProfile).first()
        if not company:
            company = CompanyProfile(company_name="Vyapaar Saarthi Default")
            
        if hasattr(message_obj, 'edit_text'):
            await message_obj.edit_text("Generating your invoice PDF...")
        else:
            await message_obj.reply_text("Generating your invoice PDF...")
            
        pdf_bytes = PDFInvoiceService.generate_invoice(order, company)
        
        await context.bot.send_document(
            chat_id=message_obj.chat_id,
            document=pdf_bytes,
            filename=f"Invoice_ORD-{order.id}.pdf",
            caption=f"Here is the invoice for Order #{order.id} ({order.customer})."
        )
    except Exception as e:
        logger.error(f"Invoice generation failed: {e}")
        await context.bot.send_message(chat_id=message_obj.chat_id, text="Error generating invoice.")
    finally:
        db.close()
