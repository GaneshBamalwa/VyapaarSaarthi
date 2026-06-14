from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.invoice import Invoice
from app.models.order import Order
from app.models.buyer import Buyer
from app.models.collections import BuyerRiskProfile, CollectionReminder
from app.agents.collections.agent import CollectionsAgent
from app.agents.collections.risk_engine import format_inr
from app.agents.collections.schemas import (
    BuyerRiskProfileOut,
    CollectionReminderOut,
    CollectionsStatsOut,
    HITLApprovalRequest,
    ManualReminderRequest,
    OverdueInvoiceOut,
)
from app.core.logging import get_logger
from pydantic import BaseModel
from datetime import timedelta
import dateutil.parser

router = APIRouter(prefix="/api/collections", tags=["Collections Agent"])
_agent = CollectionsAgent()
logger = get_logger(__name__)


# ─── Legacy request schema (keeps /analyze working) ───────────────────────────

class CollectionsRequest(BaseModel):
    invoice_id: Optional[str] = None
    customer: Optional[str] = None
    amount: Optional[float] = None
    due_days: Optional[int] = None
    previous_reminders: int = 0


# ─── Legacy endpoint (backwards compat) ──────────────────────────────────────

@router.post("/analyze")
async def analyze_collection(req: CollectionsRequest, db: Session = Depends(get_db)):
    """Analyze overdue invoice and generate Hindi reminder (legacy endpoint)."""
    invoice_id = req.invoice_id
    customer = req.customer
    amount = req.amount
    due_days = req.due_days

    if invoice_id and not (customer and amount and due_days is not None):
        inv = db.query(Invoice).filter(Invoice.invoice_number == invoice_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        customer = customer or inv.buyer_name
        amount = amount or float(inv.total or 0.0)
        if due_days is None:
            delta = (
                (datetime.utcnow().date() - inv.due_date.date()).days
                if inv.due_date
                else 10
            )
            due_days = max(0, delta)

    if not all([invoice_id, customer, amount is not None, due_days is not None]):
        raise HTTPException(
            status_code=422,
            detail="Provide invoice_id (existing) or customer+amount+due_days",
        )

    result = await _agent.invoke(
        {
            "invoice_id": invoice_id,
            "customer": customer,
            "amount": amount,
            "due_days": due_days,
            "previous_reminders": req.previous_reminders,
        }
    )
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


# ─── New autonomous endpoints ─────────────────────────────────────────────────

def _parse_delivery_date(date_str: str | None) -> date | None:
    if not date_str:
        return None
    d = date_str.lower().strip()
    today = date.today()
    if d == "today": return today
    if d == "tomorrow": return today + timedelta(days=1)
    if d == "yesterday": return today - timedelta(days=1)
    try:
        return dateutil.parser.parse(d, dayfirst=True).date()
    except Exception:
        return None

def _get_order_total(order: Order) -> float:
    return sum((i.price or 0.0) * (i.quantity or 1) for i in order.items)

@router.get("/overdue", response_model=list[OverdueInvoiceOut])
async def get_overdue_invoices(
    min_days: int = Query(default=1, ge=1),
    max_days: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    """List all overdue orders with risk tier and phone enrichment."""
    today = date.today()
    
    # We now fetch Orders instead of Invoices
    orders = db.query(Order).filter(
        Order.status.notin_(["REJECTED", "CANCELLED", "draft"]),
        Order.payment_status != "PAID"
    ).all()

    result = []
    for inv in orders:
        if not inv.customer:
            continue
            
        due_date = _parse_delivery_date(inv.delivery_date)
        if not due_date:
            continue
            
        days_overdue = (today - due_date).days
        if days_overdue < min_days:
            continue
        if max_days is not None and days_overdue > max_days:
            continue

        total_due = _get_order_total(inv)
        if total_due <= 0:
            continue

        risk_profile = db.query(BuyerRiskProfile).filter(
            BuyerRiskProfile.buyer_name == inv.customer
        ).first()
        risk_tier = risk_profile.risk_tier if risk_profile else None

        phone = _get_phone_for_buyer(db, inv.customer)
        if not phone and inv.customer_phone:
            phone = inv.customer_phone

        telegram_id = _get_telegram_for_buyer(db, inv.customer)
        if not telegram_id and getattr(inv, "telegram_chat_id", None):
            telegram_id = inv.telegram_chat_id

        has_contact = bool(phone) or bool(telegram_id)
        display_phone = phone if phone else ("Telegram User" if telegram_id else None)

        result.append(
            OverdueInvoiceOut(
                invoice_id=inv.id,
                buyer_name=inv.customer,
                buyer_phone=display_phone,
                has_phone=has_contact,
                amount_due=float(total_due),
                due_date=datetime.combine(due_date, datetime.min.time()),
                days_overdue=days_overdue,
                risk_tier=risk_tier,
            )
        )

    result.sort(key=lambda x: x.days_overdue, reverse=True)
    return result


@router.get("/risk-scores", response_model=list[BuyerRiskProfileOut])
async def get_risk_scores(
    tier: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """Get all buyer risk profiles, optionally filtered by tier."""
    query = db.query(BuyerRiskProfile)
    if tier:
        query = query.filter(BuyerRiskProfile.risk_tier == tier)
    return query.order_by(BuyerRiskProfile.avg_delay_days.desc()).all()


@router.get("/reminder-history", response_model=list[CollectionReminderOut])
async def get_reminder_history(
    status: Optional[str] = Query(default=None),
    buyer_name: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    """Paginated reminder history with optional filters."""
    query = db.query(CollectionReminder)
    if status:
        query = query.filter(CollectionReminder.status == status)
    if buyer_name:
        query = query.filter(
            CollectionReminder.buyer_name.ilike(f"%{buyer_name}%")
        )
    return (
        query.order_by(CollectionReminder.sent_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/stats", response_model=CollectionsStatsOut)
async def get_collections_stats(db: Session = Depends(get_db)):
    """Dashboard statistics for the collections module."""
    today = date.today()

    orders = db.query(Order).filter(
        Order.status.notin_(["REJECTED", "CANCELLED", "draft"]),
        Order.payment_status != "PAID"
    ).all()
    
    overdue_count = 0
    total_overdue_amount = 0.0
    
    for inv in orders:
        if not inv.customer: continue
        due_date = _parse_delivery_date(inv.delivery_date)
        if not due_date: continue
        if due_date < today:
            total = _get_order_total(inv)
            if total > 0:
                overdue_count += 1
                total_overdue_amount += float(total)

    high_risk = (
        db.query(BuyerRiskProfile)
        .filter(BuyerRiskProfile.risk_tier == "high")
        .count()
    )
    medium_risk = (
        db.query(BuyerRiskProfile)
        .filter(BuyerRiskProfile.risk_tier == "medium")
        .count()
    )
    low_risk = (
        db.query(BuyerRiskProfile)
        .filter(BuyerRiskProfile.risk_tier == "low")
        .count()
    )

    reminders_sent_today = (
        db.query(CollectionReminder)
        .filter(
            func.date(CollectionReminder.sent_at) == today,
            CollectionReminder.status == "sent",
        )
        .count()
    )
    reminders_pending_hitl = (
        db.query(CollectionReminder)
        .filter(CollectionReminder.status == "pending_hitl")
        .count()
    )

    return CollectionsStatsOut(
        total_overdue_invoices=overdue_count,
        total_overdue_amount=total_overdue_amount,
        high_risk_buyers=high_risk,
        medium_risk_buyers=medium_risk,
        low_risk_buyers=low_risk,
        reminders_sent_today=reminders_sent_today,
        reminders_pending_hitl=reminders_pending_hitl,
    )


@router.post("/send-reminder", response_model=CollectionReminderOut)
async def send_manual_reminder(
    body: ManualReminderRequest,
    db: Session = Depends(get_db),
):
    """Manually trigger a reminder for a specific invoice."""
    reminder = await _agent.send_single_reminder(db, body.invoice_id, body.override_level)
    return reminder


@router.post("/run-job")
async def trigger_job_manually(db: Session = Depends(get_db)):
    """Admin: run the full daily collections job immediately."""
    result = await _agent.run_daily_job(db)
    return {"message": "Job complete. Check server logs.", "summary": result}


@router.post("/hitl/approve", response_model=CollectionReminderOut)
async def approve_reminder(
    body: HITLApprovalRequest,
    db: Session = Depends(get_db),
):
    """Approve or reject a pending HITL reminder."""
    return await _agent.process_hitl_approval(
        db, body.reminder_id, body.approved, body.approved_by
    )


# ─── Buyer phone management ───────────────────────────────────────────────────

class SaveBuyerPhoneRequest(BaseModel):
    buyer_name: str
    phone: str


def _normalise_phone(raw: str) -> str:
    """Server-side phone cleaning. Returns +91XXXXXXXXXX format."""
    phone = raw.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if phone.startswith("whatsapp:"):
        phone = phone[len("whatsapp:"):]
    if not phone.startswith("+"):
        if phone.startswith("0"):
            phone = "+91" + phone[1:]
        elif len(phone) == 10:
            phone = "+91" + phone
        else:
            phone = "+" + phone  # best-effort
    return phone

@router.post("/mark-paid/{invoice_id}")
async def mark_payment_fulfilled(invoice_id: int, db: Session = Depends(get_db)):
    """Mark an order's payment as fulfilled (PAID)."""
    from fastapi import HTTPException
    order = db.query(Order).filter(Order.id == invoice_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    order.payment_status = "PAID"
    db.commit()
    return {"message": "Payment marked as fulfilled", "success": True}

def _get_phone_for_buyer(db: Session, buyer_name: str) -> str | None:
    """Look up phone from Buyers table."""
    if not buyer_name:
        return None
    buyer = db.query(Buyer).filter(Buyer.name == buyer_name).first()
    return buyer.phone if buyer and buyer.phone else None

def _get_telegram_for_buyer(db: Session, buyer_name: str) -> str | None:
    """Look up telegram id from Buyers table."""
    if not buyer_name:
        return None
    buyer = db.query(Buyer).filter(Buyer.name == buyer_name).first()
    return getattr(buyer, "telegram_chat_id", None) if buyer else None


@router.post("/buyers/phone")
async def save_buyer_phone(
    body: SaveBuyerPhoneRequest,
    db: Session = Depends(get_db),
):
    """Save or update phone number for a buyer. Idempotent."""
    phone = _normalise_phone(body.phone)
    buyer_name = body.buyer_name.strip()

    # Upsert into Buyers table
    buyer = db.query(Buyer).filter(Buyer.name == buyer_name).first()
    if buyer:
        buyer.phone = phone
    else:
        buyer = Buyer(name=buyer_name, phone=phone)
        db.add(buyer)

    # Also backfill any existing orders for this buyer that lack a phone
    db.query(Order).filter(
        Order.customer == buyer_name,
        Order.customer_phone.is_(None),
    ).update({"customer_phone": phone})

    db.commit()
    logger.info(f"Saved phone {phone} for buyer '{buyer_name}'")
    return {"saved": True, "phone": phone}
