from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database.session import get_db
from app.models import Invoice, Buyer, HITLQueue, SellerProfile, HITLStatus
from app.agents.gst.agent import GSTAgent
from app.utils.mock_gstn import verify_gstin, get_gstr1_summary, get_input_tax_credit
from app.websocket.manager import manager

router = APIRouter(prefix="/api/gst", tags=["GST Agent"])
gst_agent = GSTAgent()


class LineItem(BaseModel):
    name: str
    qty: float
    unit: str
    rate: float
    hsn: Optional[str] = None


class InvoiceRequest(BaseModel):
    order_id: int
    buyer_name: str
    buyer_state: str
    buyer_gstin: Optional[str] = None
    line_items: List[LineItem]


class SellerProfileRequest(BaseModel):
    name: str
    gstin: str
    state: str
    address: str


@router.post("/invoice/generate")
async def create_invoice(req: InvoiceRequest, db: Session = Depends(get_db)):
    invoice_count = db.query(Invoice).count()
    seller = db.query(SellerProfile).first()
    if not seller:
        raise HTTPException(status_code=500, detail="Seller profile not configured")
        
    seller_data = {
        "name": seller.name,
        "gstin": seller.gstin,
        "state": seller.state,
        "address": seller.address
    }
    
    invoice_data = await gst_agent.generate_gst_invoice(
        order_id=req.order_id,
        buyer_name=req.buyer_name,
        buyer_state=req.buyer_state,
        buyer_gstin=req.buyer_gstin,
        line_items=[item.model_dump() for item in req.line_items],
        invoice_count=invoice_count,
        seller_profile=seller_data,
    )

    # Push to HITL queue for owner approval
    hitl_entry = HITLQueue(
        action_type="invoice_draft",
        order_id=req.order_id,
        payload=invoice_data,
        status=HITLStatus.PENDING,
        reason="GST Invoice Draft Approval Needed",
    )
    db.add(hitl_entry)
    db.commit()
    db.refresh(hitl_entry)

    # Emit the event via websocket
    await manager.emit_hitl_event(hitl_entry.id, "PENDING", invoice_data)

    return {"invoice": invoice_data, "hitl_id": hitl_entry.id, "requires_approval": True}


@router.get("/seller-profile")
async def get_seller_profile(db: Session = Depends(get_db)):
    profile = db.query(SellerProfile).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Seller profile not found")
    return {
        "id": profile.id,
        "name": profile.name,
        "gstin": profile.gstin,
        "state": profile.state,
        "address": profile.address,
    }


@router.put("/seller-profile")
async def update_seller_profile(req: SellerProfileRequest, db: Session = Depends(get_db)):
    profile = db.query(SellerProfile).first()
    if not profile:
        profile = SellerProfile()
        db.add(profile)
    
    profile.name = req.name
    profile.gstin = req.gstin
    profile.state = req.state
    profile.address = req.address
    db.commit()
    db.refresh(profile)
    return {"message": "Seller profile updated successfully", "profile": req.model_dump()}


@router.get("/invoices")
async def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).order_by(Invoice.created_at.desc()).all()
    return [
        {
            "id": i.id,
            "invoice_number": i.invoice_number,
            "buyer_name": i.buyer_name,
            "buyer_state": i.buyer_state,
            "subtotal": i.subtotal,
            "cgst": i.cgst,
            "sgst": i.sgst,
            "igst": i.igst,
            "total": i.total,
            "tax_type": i.tax_type,
            "status": i.status,
            "due_date": i.due_date.isoformat() if i.due_date else None,
            "created_at": i.created_at.isoformat(),
        }
        for i in invoices
    ]


@router.get("/gstin/verify/{gstin}")
async def verify_gstin_endpoint(gstin: str):
    result = verify_gstin(gstin)
    return result


@router.get("/gstr1/{gstin}")
async def get_gstr1(gstin: str, month: int = 1, year: int = 2024):
    return get_gstr1_summary(gstin, month, year)


@router.get("/itc/{gstin}")
async def get_itc(gstin: str):
    return get_input_tax_credit(gstin)


@router.post("/validate-return")
async def validate_return(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).filter(Invoice.status.in_(["approved", "paid"])).all()
    invoice_list = [
        {
            "invoice_number": i.invoice_number,
            "buyer_name": i.buyer_name,
            "buyer_gstin": None,
            "subtotal": i.subtotal,
            "total": i.total,
        }
        for i in invoices
    ]
    result = await gst_agent.validate_gstr_return(invoice_list)
    return result


@router.get("/hsn/lookup")
async def lookup_hsn_code(product: str):
    result = gst_agent.lookup_hsn(product)
    return {"product": product, **result}
