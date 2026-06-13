from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import SessionLocal, Order, OrderHITLQueue
from services.intake_service import process_order, resume_after_hitl

router = APIRouter(prefix="/api/intake", tags=["intake"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class OrderRequest(BaseModel):
    text: str
    input_type: str = "text"  # text | voice | ocr


class HITLReview(BaseModel):
    approved: bool
    edited_payload: Optional[dict] = {}
    reviewer_notes: Optional[str] = ""


@router.post("/order")
async def submit_order(req: OrderRequest, db: Session = Depends(get_db)):
    return await process_order(req.text, req.input_type, db)


@router.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).order_by(Order.created_at.desc()).limit(50).all()
    return [
        {
            "id": o.id,
            "customer": o.customer,
            "status": o.status,
            "confidence": o.confidence,
            "input_type": o.input_type,
            "created_at": str(o.created_at),
        }
        for o in orders
    ]


@router.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": order.id,
        "customer": order.customer,
        "status": order.status,
        "confidence": order.confidence,
        "input_type": order.input_type,
        "raw_input": order.raw_input,
        "delivery_date": str(order.delivery_date) if order.delivery_date else None,
        "notes": order.notes,
        "items": [
            {"name": i.name, "quantity": i.quantity, "unit": i.unit, "price": i.price}
            for i in order.items
        ],
        "created_at": str(order.created_at),
    }


@router.get("/hitl-queue")
def list_hitl_queue(db: Session = Depends(get_db)):
    items = db.query(OrderHITLQueue).filter(OrderHITLQueue.status == "pending").all()
    return [
        {
            "id": h.id,
            "order_id": h.order_id,
            "reason": h.reason,
            "payload": h.payload,
            "created_at": str(h.created_at),
        }
        for h in items
    ]


@router.post("/hitl-queue/{hitl_id}/review")
async def review_hitl(hitl_id: int, body: HITLReview, db: Session = Depends(get_db)):
    return await resume_after_hitl(
        hitl_id, body.approved, body.edited_payload or {}, body.reviewer_notes or "", db
    )
