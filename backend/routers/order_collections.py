from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import SessionLocal, Invoice
from agents.collections_agent import run as collections_run

router = APIRouter(prefix="/api/collections", tags=["collections"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class CollectionsRequest(BaseModel):
    invoice_id: Optional[str] = None
    customer: Optional[str] = None
    amount: Optional[float] = None
    due_days: Optional[int] = None
    previous_reminders: int = 0


@router.post("/analyze")
async def analyze_collection(req: CollectionsRequest, db: Session = Depends(get_db)):
    invoice_id = req.invoice_id
    customer = req.customer
    amount = req.amount
    due_days = req.due_days

    if invoice_id and not (customer and amount and due_days is not None):
        inv = db.query(Invoice).filter(Invoice.invoice_number == invoice_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        from datetime import datetime
        customer = customer or inv.buyer_name
        amount = amount or float(inv.total or 0)
        if due_days is None:
            delta = (datetime.utcnow().date() - inv.due_date.date()).days if inv.due_date else 10
            due_days = max(0, delta)

    if not all([invoice_id, customer, amount is not None, due_days is not None]):
        raise HTTPException(status_code=422, detail="Provide invoice_id (existing) or customer+amount+due_days")

    return await collections_run(invoice_id, customer, amount, due_days, req.previous_reminders)


@router.get("/overdue")
def list_overdue_invoices(db: Session = Depends(get_db)):
    from datetime import datetime
    invoices = db.query(Invoice).filter(Invoice.status == "overdue").all()
    result = []
    for inv in invoices:
        delta = (datetime.utcnow().date() - inv.due_date.date()).days if inv.due_date else 0
        result.append({
            "invoice_id": inv.invoice_number,
            "customer": inv.buyer_name,
            "amount": float(inv.total or 0),
            "due_days": max(0, delta),
            "status": inv.status,
        })
    return result
