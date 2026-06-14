"""
Smart Collections Agent — autonomous daily payment follow-up.

Inherits from BaseAgent (matches project pattern).
The original .invoke() API for one-off reminder generation is preserved
so the existing /api/collections/analyze endpoint keeps working.
New methods handle the full daily job, manual triggers, and HITL approvals.
"""
import json
import time
from datetime import date, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.collections.prompt import COLLECTIONS_SYSTEM_PROMPT, COLLECTIONS_USER_TEMPLATE
from app.agents.collections.message_generator import generate_reminder_message
from app.agents.collections.risk_engine import (
    calculate_risk_tier,
    format_inr,
    update_all_risk_scores,
)
from app.agents.collections.whatsapp_service import send_whatsapp_message
from app.core.gemini_client import get_gemini_client
from app.core.config import get_settings
from app.models.collections import BuyerRiskProfile, CollectionReminder
from app.models.invoice import Invoice
from app.models.buyer import Buyer

settings = get_settings()


class CollectionsAgent(BaseAgent):
    name = "CollectionsAgent"

    # ─── Legacy one-off invoke (keeps /api/collections/analyze working) ───────

    async def invoke(self, input_data: dict, **kwargs) -> dict[str, Any]:
        """
        input_data: {
            "invoice_id": str,
            "customer": str,
            "amount": float,
            "due_days": int,
            "previous_reminders": int (default 0)
        }
        """
        invoice_id = input_data.get("invoice_id", "")
        customer = input_data.get("customer", "Customer")
        amount = input_data.get("amount", 0)
        due_days = input_data.get("due_days", 0)
        previous_reminders = input_data.get("previous_reminders", 0)

        await self._emit("running", "analyzing_invoice", data={"invoice_id": invoice_id})
        start = time.time()

        try:
            client = get_gemini_client()
            prompt = COLLECTIONS_USER_TEMPLATE.format(
                invoice_id=invoice_id,
                customer=customer,
                amount=amount,
                due_days=due_days,
                previous_reminders=previous_reminders,
            )

            response = client.models.generate_content(
                model=settings.GEMINI_FLASH_MODEL,
                contents=prompt,
                config={
                    "system_instruction": COLLECTIONS_SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                },
            )

            data = json.loads(response.text.strip())
            duration_ms = int((time.time() - start) * 1000)

            await self._emit(
                "completed",
                "reminder_generated",
                data={"risk": data.get("risk"), "invoice_id": invoice_id},
            )
            return self._success(data, duration_ms=duration_ms)

        except Exception as e:
            self.logger.error(f"CollectionsAgent error: {e}")
            await self._emit("failed", "agent_error", error=str(e))
            return self._failure(str(e))

    # ─── Daily autonomous job ─────────────────────────────────────────────────

    async def run_daily_job(self, db: Session) -> dict:
        """Main daily job. Returns summary dict."""
        today = date.today()
        summary = {
            "invoices_checked": 0,
            "reminders_sent": 0,
            "reminders_failed": 0,
            "pending_hitl": 0,
            "skipped_already_sent": 0,
            "risk_scores_updated": 0,
        }

        overdue = self._fetch_overdue_invoices(db)
        summary["invoices_checked"] = len(overdue)

        for inv, days_overdue in overdue:
            # Skip if already sent today
            already_sent = db.query(CollectionReminder).filter(
                CollectionReminder.invoice_id == inv.id,
                func.date(CollectionReminder.sent_at) == today,
            ).first()
            if already_sent:
                summary["skipped_already_sent"] += 1
                continue

            # Determine reminder level
            level = 2 if days_overdue > 7 else 1

            buyer_name = inv.customer or "Unknown"

            # Get risk profile
            risk_profile = db.query(BuyerRiskProfile).filter(
                BuyerRiskProfile.buyer_name == buyer_name
            ).first()
            risk_tier = risk_profile.risk_tier if risk_profile else "low"

            amount_due = float(__import__('app.routers.collections').routers.collections._get_order_total(inv))

            # HITL gate: HIGH risk + Level 2 → queue for human approval
            if risk_tier == "high" and level == 2:
                reminder = CollectionReminder(
                    invoice_id=inv.id,
                    buyer_name=buyer_name,
                    buyer_phone=None,
                    amount_due=amount_due,
                    days_overdue=days_overdue,
                    level=level,
                    message_text="[Pending generation — awaiting HITL approval]",
                    status="pending_hitl",
                )
                db.add(reminder)
                db.commit()
                summary["pending_hitl"] += 1
                self.logger.info(
                    f"HITL queued for {buyer_name} order #{inv.id} "
                    f"(high risk, level 2)"
                )
                continue

            # Generate message via Gemini
            past_late_count = risk_profile.payment_count if risk_profile else 0
            message = await generate_reminder_message(
                buyer_name=buyer_name,
                invoice_id=inv.id,
                amount=amount_due,
                days_overdue=days_overdue,
                level=level,
                business_name=settings.BUSINESS_NAME,
                past_late_count=past_late_count,
            )

            # Order model might have customer_phone or telegram_chat_id
            phone = self._get_buyer_phone(db, inv)
            telegram_id = self._get_buyer_telegram_id(db, inv)
            
            if telegram_id:
                from app.agents.collections.telegram_service import send_telegram_message
                result = await send_telegram_message(telegram_id, message)
            elif phone:
                result = await send_whatsapp_message(phone, message)
            else:
                self.logger.info(
                    f"No phone/Telegram for {buyer_name} (order #{inv.id}) — "
                    f"saving reminder without send"
                )
                result = {"success": True, "sid": "no-phone-no-telegram", "error": None}

            reminder = CollectionReminder(
                invoice_id=inv.id,
                buyer_name=buyer_name,
                buyer_phone=phone,
                amount_due=amount_due,
                days_overdue=days_overdue,
                level=level,
                message_text=message,
                status="sent" if result["success"] else "failed",
                whatsapp_sid=result["sid"],
            )
            db.add(reminder)
            db.commit()

            if result["success"]:
                summary["reminders_sent"] += 1
            else:
                summary["reminders_failed"] += 1

        # Update risk scores
        summary["risk_scores_updated"] = update_all_risk_scores(db)
        return summary

    # ─── Manual single-invoice trigger ───────────────────────────────────────

    async def send_single_reminder(
        self,
        db: Session,
        invoice_id: int,
        override_level: int | None = None,
    ) -> CollectionReminder:
        """Manual trigger for one order. Bypasses HITL gate."""
        from app.models.order import Order
        inv = db.query(Order).filter(Order.id == invoice_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Order not found")

        today = date.today()
        due_date = __import__('app.routers.collections').routers.collections._parse_delivery_date(inv.delivery_date)
        days_overdue = 0
        if due_date and due_date < today:
            days_overdue = (today - due_date).days

        level = override_level if override_level in (1, 2) else (
            2 if days_overdue > 7 else 1
        )
        
        amount_due = float(__import__('app.routers.collections').routers.collections._get_order_total(inv))
        buyer_name = inv.customer or "Unknown"

        message = await generate_reminder_message(
            buyer_name=buyer_name,
            invoice_id=inv.id,
            amount=amount_due,
            days_overdue=days_overdue,
            level=level,
            business_name=settings.BUSINESS_NAME,
        )

        phone = self._get_buyer_phone(db, inv)
        telegram_id = self._get_buyer_telegram_id(db, inv)
        
        if telegram_id:
            from app.agents.collections.telegram_service import send_telegram_message
            result = await send_telegram_message(telegram_id, message)
        elif phone:
            result = await send_whatsapp_message(phone, message)
        else:
            result = {"success": True, "sid": "no-phone-no-telegram", "error": None}

        reminder = CollectionReminder(
            invoice_id=inv.id,
            buyer_name=buyer_name,
            buyer_phone=phone,
            amount_due=amount_due,
            days_overdue=days_overdue,
            level=level,
            message_text=message,
            status="sent" if result["success"] else "failed",
            whatsapp_sid=result["sid"],
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder

    # ─── HITL approval processing ─────────────────────────────────────────────

    async def process_hitl_approval(
        self,
        db: Session,
        reminder_id: int,
        approved: bool,
        approved_by: str,
    ) -> CollectionReminder:
        """Process manager approval/rejection of a pending reminder."""
        reminder = db.query(CollectionReminder).filter(
            CollectionReminder.id == reminder_id
        ).first()
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        if reminder.status != "pending_hitl":
            raise HTTPException(
                status_code=400,
                detail=f"Reminder status is '{reminder.status}', not pending_hitl",
            )

        if approved:
            # Generate fresh message now that it's approved
            message = await generate_reminder_message(
                buyer_name=reminder.buyer_name,
                invoice_id=reminder.invoice_id,
                amount=reminder.amount_due,
                days_overdue=reminder.days_overdue,
                level=reminder.level,
                business_name=settings.BUSINESS_NAME,
            )
            reminder.message_text = message

            if reminder.buyer_phone:
                result = await send_whatsapp_message(reminder.buyer_phone, message)
                reminder.whatsapp_sid = result["sid"]

            reminder.status = "approved"
        else:
            reminder.status = "rejected"

        reminder.approved_by = approved_by
        reminder.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(reminder)
        return reminder

    # ─── Internal helpers ─────────────────────────────────────────────────────

    def _get_buyer_phone(self, db: Session, order_or_invoice) -> str | None:
        """
        Phone lookup priority:
          1. order/invoice.customer_phone (captured at intake from WhatsApp)
          2. Buyers table lookup by buyer_name / customer
          3. None
        """
        # Priority 1 — direct field (Orders have it, Invoices do not)
        phone = getattr(order_or_invoice, "customer_phone", None)
        if phone:
            return phone

        # Priority 2 — Buyers table by name
        buyer_name = getattr(
            order_or_invoice, "buyer_name",
            getattr(order_or_invoice, "customer", None)
        )
        if buyer_name:
            buyer = db.query(Buyer).filter(Buyer.name == buyer_name).first()
            if buyer and buyer.phone:
                return buyer.phone

        return None
        
    def _get_buyer_telegram_id(self, db: Session, order_or_invoice) -> str | None:
        tid = getattr(order_or_invoice, "telegram_chat_id", None)
        if tid:
            return tid

        buyer_name = getattr(
            order_or_invoice, "buyer_name",
            getattr(order_or_invoice, "customer", None)
        )
        if buyer_name:
            buyer = db.query(Buyer).filter(Buyer.name == buyer_name).first()
            if buyer and buyer.telegram_chat_id:
                return buyer.telegram_chat_id

        return None

    def _fetch_overdue_invoices(self, db: Session) -> list:
        """
        Fetches orders where delivery_date < today and status is not cancelled/draft.
        Returns a list of tuples (Order, days_overdue).
        """
        from app.models.order import Order
        from app.routers.collections import _parse_delivery_date

        today = date.today()
        orders = db.query(Order).filter(
            Order.status.notin_(["REJECTED", "CANCELLED", "draft"])
        ).all()
        
        overdue = []
        for inv in orders:
            due_date = _parse_delivery_date(inv.delivery_date)
            if due_date and due_date < today:
                overdue.append((inv, (today - due_date).days))
        return overdue
