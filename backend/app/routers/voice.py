from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import uuid

from app.database.session import get_db
from app.models import ChatMessage, Invoice, Buyer, Order, GSTNotice
from app.models.expense import ExpenseEntry
from app.agents.voice.agent import VoiceAgent

router = APIRouter(prefix="/api/voice", tags=["Voice & Chat"])
voice_agent = VoiceAgent()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    generate_audio: bool = False


class ChatResponse(BaseModel):
    session_id: str
    user_message: str
    response: str
    intent: str
    audio_url: Optional[str] = None
    timestamp: str
    action_result: Optional[dict] = None


def _build_db_context(db: Session) -> dict:
    """Pull live business metrics from the DB to give the AI real context."""
    try:
        buyers = db.query(Buyer).limit(10).all()
        invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).limit(20).all()
        overdue = [i for i in invoices if i.status == "overdue"]
        recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
        notices = db.query(GSTNotice).filter(GSTNotice.status == "unreviewed").all()

        total_revenue = db.query(func.sum(Invoice.total)).filter(
            Invoice.status.in_(["paid", "approved"])).scalar() or 0
        outstanding = db.query(func.sum(Invoice.total)).filter(
            Invoice.status == "overdue").scalar() or 0

        current_month = datetime.utcnow().strftime("%Y-%m")
        expenses = db.query(ExpenseEntry).filter(
            ExpenseEntry.month == current_month,
            ExpenseEntry.is_deleted == False
        ).all()
        total_expenses = sum(e.amount for e in expenses)

        return {
            "seller": {
                "gstin": "27AAPFU0939F1ZV",
                "state": "Maharashtra",
                "total_revenue_all_time": round(float(total_revenue), 2),
                "total_outstanding": round(float(outstanding), 2),
            },
            "buyers": [
                {"name": b.name, "state": b.state, "risk_tier": b.risk_tier,
                 "outstanding": round(float(b.total_outstanding or 0), 2)}
                for b in buyers
            ],
            "recent_invoices": [
                {"number": i.invoice_number, "buyer": i.buyer_name,
                 "total": round(float(i.total), 2), "status": i.status,
                 "due_date": i.due_date.strftime("%Y-%m-%d") if i.due_date else None}
                for i in invoices[:8]
            ],
            "overdue_invoices": [
                {"number": i.invoice_number, "buyer": i.buyer_name,
                 "total": round(float(i.total), 2),
                 "days_overdue": (datetime.utcnow() - i.due_date).days if i.due_date else 0}
                for i in overdue
            ],
            "recent_orders": [
                {"id": o.id, "customer": o.customer, "status": o.status.value if hasattr(o.status, "value") else o.status,
                 "input": o.raw_input[:80]}
                for o in recent_orders
            ],
            "pending_notices": len(notices),
            "gst_filing": {
                "gstr1_due": (datetime.utcnow() + timedelta(days=8)).strftime("%Y-%m-%d"),
                "gstr3b_due": (datetime.utcnow() + timedelta(days=15)).strftime("%Y-%m-%d"),
            },
            "expenses_this_month": {
                "total_amount": round(float(total_expenses), 2),
                "details": [
                    {"category": e.category, "vendor": e.vendor_name, "amount": round(float(e.amount), 2), "is_paid": e.is_paid}
                    for e in expenses[:10]
                ]
            }
        }
    except Exception as e:
        print(f"[VoiceRouter] DB context error: {e}")
        return {}


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    session_id = req.session_id or str(uuid.uuid4())

    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(6)
        .all()
    )
    history_list = [{"role": m.role, "content": m.content} for m in reversed(history)]

    # Build real DB context for the AI
    db_context = _build_db_context(db)

    result = await voice_agent.chat(req.message, session_id, history_list, db_context)

    # Persist conversation user message
    db.add(ChatMessage(session_id=session_id, role="user", content=req.message))

    # If order intent → create order in DB via intake pipeline ONLY if price conditions met
    action_result = None
    if result["intent"] == "order" and result.get("execute_order", False):
        try:
            from app.services.intake_service import IntakeService
            service = IntakeService(db)
            action_result = await service.process_text_order(req.message)
        except Exception as e:
            action_result = {"error": str(e)}
    elif result["intent"] == "fulfill":
        try:
            import re
            match = re.search(r'\b\d+\b', req.message)
            if match:
                order_id = int(match.group())
                from app.repositories.order_repository import OrderRepository
                from app.models.order import OrderStatus
                from app.websocket.manager import manager
                repo = OrderRepository(db)
                order = repo.update_status(order_id, OrderStatus.COMPLETED)
                if order:
                    await manager.emit_order_event(order.id, order.status.value, {"customer": order.customer})
                    action_result = {"status": "success", "order_id": order_id}
                else:
                    action_result = {"status": "error", "message": "Order not found"}
            else:
                action_result = {"status": "error", "message": "No order ID found in the request"}
        except Exception as e:
            action_result = {"error": str(e)}

    audio_url = None
    if req.generate_audio:
        audio_url = await voice_agent.synthesize(result["response"])

    # Persist assistant response
    db.add(ChatMessage(
        session_id=session_id, role="assistant",
        content=result["response"], audio_url=audio_url
    ))
    db.commit()

    return ChatResponse(**result, audio_url=audio_url, action_result=action_result)


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str = Form("hi-IN")):
    audio_bytes = await audio.read()
    transcript = await voice_agent.transcribe(audio_bytes, language)
    return {"transcript": transcript, "language": language}


@router.post("/synthesize")
async def synthesize(text: str = Form(...), language: str = Form("hi-IN")):
    audio_url = await voice_agent.synthesize(text, language)
    return {"audio_url": audio_url, "text": text}


@router.post("/weekly-briefing")
async def weekly_briefing(db: Session = Depends(get_db)):
    """Generate a Hindi briefing using real DB metrics."""
    orders = db.query(Order).filter(Order.status.notin_(["REJECTED", "CANCELLED", "draft"])).all()
    
    today = datetime.utcnow().date()
    
    orders_pending_this_week = []
    payment_dues = []
    monthly_revenue = 0.0
    
    import dateutil.parser
    for o in orders:
        total = sum((i.price or 0.0) * (i.quantity or 1) for i in o.items)
        if total <= 0:
            continue
            
        d_date = None
        if o.delivery_date:
            try:
                if "today" in o.delivery_date.lower(): d_date = today
                elif "tomorrow" in o.delivery_date.lower(): d_date = today + timedelta(days=1)
                else: d_date = dateutil.parser.parse(o.delivery_date, dayfirst=True).date()
            except:
                pass
                
        if d_date:
            # Monthly Revenue
            if d_date.year == today.year and d_date.month == today.month:
                monthly_revenue += total
                
            # Pending deliveries this week
            status_val = getattr(o.status, "value", o.status)
            if status_val != "COMPLETED":
                if today <= d_date <= today + timedelta(days=7):
                    orders_pending_this_week.append({"customer": o.customer, "amount": total})
            
            # Payment dues this week (including already overdue)
            if getattr(o, "payment_status", "PENDING") != "PAID":
                if d_date <= today + timedelta(days=7):
                    payment_dues.append({"customer": o.customer, "amount": total})

    business_data = {
        "monthly_order_revenue": round(monthly_revenue, 2),
        "orders_pending_this_week_count": len(orders_pending_this_week),
        "orders_pending_this_week_details": orders_pending_this_week[:3],
        "payment_dues_this_week_count": len(payment_dues),
        "total_payment_dues_amount": sum(x["amount"] for x in payment_dues),
        "payment_dues_details": payment_dues[:3]
    }
    result = await voice_agent.weekly_briefing(business_data)
    return result


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str, db: Session = Depends(get_db)):
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "audio_url": m.audio_url,
            "timestamp": m.created_at.isoformat(),
        }
        for m in messages
    ]
