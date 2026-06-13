from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_db, HITLQueue, Invoice
from utils.ws_manager import ws_manager

router = APIRouter(prefix="/api/hitl", tags=["Human-in-the-Loop"])


class HITLDecision(BaseModel):
    action: str  # approve | reject | edit
    edited_payload: Optional[dict] = None


@router.get("/queue")
async def get_queue(db: Session = Depends(get_db)):
    items = db.query(HITLQueue).filter(HITLQueue.status == "pending").order_by(HITLQueue.created_at.asc()).all()
    return [
        {
            "id": i.id,
            "action_type": i.action_type,
            "payload": i.payload,
            "status": i.status,
            "created_at": i.created_at.isoformat(),
        }
        for i in items
    ]


@router.post("/queue/{item_id}/decide")
async def decide(item_id: int, decision: HITLDecision, db: Session = Depends(get_db)):
    item = db.query(HITLQueue).filter(HITLQueue.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="HITL item not found")

    payload = decision.edited_payload or item.payload
    item.status = decision.action if decision.action in ("approved", "rejected") else "approved"
    item.resolved_at = datetime.utcnow()

    if decision.action in ("approve", "approved") and item.action_type == "invoice_draft":
        inv_data = payload
        invoice = Invoice(
            invoice_number=inv_data.get("invoice_number"),
            order_id=inv_data.get("order_id"),
            buyer_name=inv_data.get("buyer", {}).get("name", ""),
            buyer_state=inv_data.get("buyer", {}).get("state", ""),
            line_items=inv_data.get("line_items", []),
            subtotal=inv_data.get("subtotal", 0),
            cgst=inv_data.get("cgst", 0),
            sgst=inv_data.get("sgst", 0),
            igst=inv_data.get("igst", 0),
            total=inv_data.get("grand_total", 0),
            tax_type=inv_data.get("tax_type", ""),
            status="approved",
        )
        db.add(invoice)
        await ws_manager.broadcast("HITL", "approved", f"Invoice {inv_data.get('invoice_number')} approved and saved")

    db.commit()
    return {"item_id": item_id, "status": item.status, "message": f"Item {decision.action}d successfully"}
