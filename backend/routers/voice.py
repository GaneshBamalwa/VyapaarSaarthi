from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
import uuid

from database import get_db, ChatMessage, Invoice, Buyer, Order, GSTNotice
from agents.voice_agent import (
    process_chat_message, transcribe_audio, synthesize_speech, generate_weekly_briefing
)

router = APIRouter(prefix="/api/voice", tags=["Voice & Chat"])


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
                {"id": o.id, "customer": o.customer, "status": o.status,
                 "input": o.raw_input[:80]}
                for o in recent_orders
            ],
            "pending_notices": len(notices),
            "gst_filing": {
                "gstr1_due": (datetime.utcnow() + timedelta(days=8)).strftime("%Y-%m-%d"),
                "gstr3b_due": (datetime.utcnow() + timedelta(days=15)).strftime("%Y-%m-%d"),
            },
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

    result = await process_chat_message(req.message, session_id, history_list, db_context)

    # Persist conversation
    db.add(ChatMessage(session_id=session_id, role="user", content=req.message))

    # If order intent → create order in DB via intake pipeline
    action_result = None
    if result["intent"] == "order":
        try:
            from services.intake_service import process_order
            action_result = await process_order(req.message, "voice_chat", db)
        except Exception as e:
            action_result = {"error": str(e)}

    audio_url = None
    if req.generate_audio:
        audio_url = await synthesize_speech(result["response"])

    db.add(ChatMessage(
        session_id=session_id, role="assistant",
        content=result["response"], audio_url=audio_url
    ))
    db.commit()

    return ChatResponse(**result, audio_url=audio_url, action_result=action_result)


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...), language: str = Form("hi-IN")):
    audio_bytes = await audio.read()
    transcript = await transcribe_audio(audio_bytes, language)
    return {"transcript": transcript, "language": language}


@router.post("/synthesize")
async def synthesize(text: str = Form(...), language: str = Form("hi-IN")):
    audio_url = await synthesize_speech(text, language)
    return {"audio_url": audio_url, "text": text}


@router.post("/weekly-briefing")
async def weekly_briefing(db: Session = Depends(get_db)):
    """Generate a Hindi briefing using real DB metrics."""
    invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).limit(30).all()
    overdue  = [i for i in invoices if i.status == "overdue"]
    paid_this_week = [
        i for i in invoices
        if i.status in ("paid", "approved")
        and i.created_at and i.created_at >= datetime.utcnow() - timedelta(days=7)
    ]

    top_buyer = None
    if invoices:
        from collections import Counter
        buyer_counts = Counter(i.buyer_name for i in invoices)
        top_buyer = buyer_counts.most_common(1)[0][0]

    business_data = {
        "weekly_revenue": round(sum(float(i.total) for i in paid_this_week), 2),
        "total_invoices_this_week": len(paid_this_week),
        "outstanding_receivables": round(sum(float(i.total) for i in overdue), 2),
        "overdue_count": len(overdue),
        "overdue_details": [
            {"buyer": i.buyer_name, "amount": round(float(i.total), 2),
             "days": (datetime.utcnow() - i.due_date).days if i.due_date else 0}
            for i in overdue[:3]
        ],
        "top_buyer": top_buyer,
        "gstr1_due_days": 8,
        "gstr3b_due_days": 15,
    }
    result = await generate_weekly_briefing(business_data)
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
