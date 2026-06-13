from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database.session import get_db
from app.models import Invoice
from app.agents.collections.agent import CollectionsAgent

router = APIRouter(prefix="/api/collections", tags=["Collections Agent"])
_agent = CollectionsAgent()


class CollectionsRequest(BaseModel):
    invoice_id: Optional[str] = None
    customer: Optional[str] = None
    amount: Optional[float] = None
    due_days: Optional[int] = None
    previous_reminders: int = 0


@router.post("/analyze")
async def analyze_collection(req: CollectionsRequest, db: Session = Depends(get_db)):
    """Analyze overdue invoice and generate Hindi reminder."""
    invoice_id = req.invoice_id
    customer = req.customer
    amount = req.amount
    due_days = req.due_days

    # Look up invoice details in DB if only ID is provided
    if invoice_id and not (customer and amount and due_days is not None):
        inv = db.query(Invoice).filter(Invoice.invoice_number == invoice_id).first()
        if not inv:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        customer = customer or inv.buyer_name
        amount = amount or float(inv.total or 0.0)
        if due_days is None:
            delta = (datetime.utcnow().date() - inv.due_date.date()).days if inv.due_date else 10
            due_days = max(0, delta)

    if not all([invoice_id, customer, amount is not None, due_days is not None]):
        raise HTTPException(
            status_code=422,
            detail="Provide invoice_id (existing) or customer+amount+due_days"
        )

    agent_input = {
        "invoice_id": invoice_id,
        "customer": customer,
        "amount": amount,
        "due_days": due_days,
        "previous_reminders": req.previous_reminders,
    }

    result = await _agent.invoke(agent_input)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/overdue")
def list_overdue_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).filter(Invoice.status == "overdue").all()
    result = []
    for inv in invoices:
        delta = (datetime.utcnow().date() - inv.due_date.date()).days if inv.due_date else 0
        result.append({
            "invoice_id": inv.invoice_number,
            "customer": inv.buyer_name,
            "amount": float(inv.total or 0.0),
            "due_days": max(0, delta),
            "status": inv.status,
        })
    return result
