from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.database.session import get_db
from app.models import GSTNotice, Invoice, NoticeType, MSMEScheme
from app.agents.compliance.agent import ComplianceAgent

router = APIRouter(prefix="/api/compliance", tags=["Compliance Agent"])
compliance_agent = ComplianceAgent()


class NoticeRequest(BaseModel):
    raw_text: str


class SchemeRequest(BaseModel):
    annual_turnover: float
    employee_count: int = 5
    category: str = "manufacturing"


class MSMESchemeCreate(BaseModel):
    name: str
    min_turnover: float
    max_turnover: float
    benefit: str
    eligibility: str
    apply_url: str


class NoticeTypeCreate(BaseModel):
    code: str
    description: str


@router.post("/notice/translate")
async def translate_notice(req: NoticeRequest, db: Session = Depends(get_db)):
    notice_types = db.query(NoticeType).all()
    notice_types_dict = {nt.code: nt.description for nt in notice_types}
    
    try:
        result = await compliance_agent.translate_gst_notice(req.raw_text, notice_types_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    notice = GSTNotice(
        raw_text=req.raw_text,
        translated_hindi=result.get("hindi_translation"),
        action_items=result.get("action_items"),
        status="unreviewed",
    )
    db.add(notice)
    db.commit()
    db.refresh(notice)

    return {"notice_id": notice.id, **result}


@router.get("/notices")
async def list_notices(db: Session = Depends(get_db)):
    notices = db.query(GSTNotice).order_by(GSTNotice.created_at.desc()).all()
    return [
        {
            "id": n.id,
            "raw_text": n.raw_text[:120] + "..." if len(n.raw_text) > 120 else n.raw_text,
            "translated_hindi": n.translated_hindi,
            "action_items": n.action_items,
            "status": n.status,
            "created_at": n.created_at.isoformat(),
        }
        for n in notices
    ]


@router.get("/calendar/{gstin}")
async def compliance_calendar(gstin: str, db: Session = Depends(get_db)):
    """Build compliance calendar from real DB invoices."""
    now = datetime.utcnow()
    month, year = now.month, now.year

    # Derive filing status from DB
    paid_invoices = db.query(Invoice).filter(Invoice.status.in_(["paid", "approved"])).all()
    overdue_count = db.query(Invoice).filter(Invoice.status == "overdue").count()

    # Compute real ITC from invoices (input = 40% of tax paid estimate)
    total_tax = sum((i.cgst + i.sgst + i.igst) for i in paid_invoices)
    itc_available = round(total_tax * 0.4, 2)
    itc_utilized  = round(total_tax * 0.2, 2)

    deadlines = []
    for i in range(3):
        m = ((month - 1 + i) % 12) + 1
        y = year + ((month - 1 + i) // 12)
        # GSTR-1 filed if we have invoices from that month
        month_invoices = [inv for inv in paid_invoices
                          if inv.created_at and inv.created_at.month == m and inv.created_at.year == y]
        deadlines.append({
            "month": f"{m:02d}/{y}",
            "gstr1_due": f"{y}-{m:02d}-11",
            "gstr3b_due": f"{y}-{m:02d}-20",
            "gstr1_status": "Filed" if (i == 0 and month_invoices) else ("Filed" if i < 0 else "Pending"),
            "gstr3b_status": "Filed" if i < 0 else "Pending",
            "invoice_count": len(month_invoices),
        })

    alerts = []
    if overdue_count > 0:
        alerts.append(f"{overdue_count} invoices are overdue — may affect ITC claims")
    alerts.append(f"GSTR-3B due on {deadlines[0]['gstr3b_due']} — file on time to avoid ₹50/day penalty")

    return {
        "gstin": gstin,
        "current_period": f"{month:02d}/{year}",
        "deadlines": deadlines,
        "itc_available": itc_available,
        "itc_utilized": itc_utilized,
        "itc_balance": round(itc_available - itc_utilized, 2),
        "next_due_date": deadlines[0]["gstr3b_due"],
        "alerts": alerts,
    }


@router.post("/schemes/match")
async def find_schemes(req: SchemeRequest, db: Session = Depends(get_db)):
    db_schemes = db.query(MSMEScheme).all()
    schemes_list = [
        {
            "name": s.name,
            "min_turnover": s.min_turnover,
            "max_turnover": s.max_turnover,
            "benefit": s.benefit,
            "eligibility": s.eligibility,
            "apply_url": s.apply_url,
        }
        for s in db_schemes
    ]
    schemes = await compliance_agent.match_msme_schemes(req.annual_turnover, req.employee_count, req.category, schemes_list)
    return {"matched_schemes": schemes, "total_matched": len(schemes)}


@router.get("/schemes")
async def list_schemes(db: Session = Depends(get_db)):
    schemes = db.query(MSMEScheme).all()
    return schemes


@router.post("/schemes")
async def create_scheme(req: MSMESchemeCreate, db: Session = Depends(get_db)):
    new_scheme = MSMEScheme(**req.model_dump())
    db.add(new_scheme)
    db.commit()
    db.refresh(new_scheme)
    return new_scheme


@router.get("/notice-types")
async def list_notice_types(db: Session = Depends(get_db)):
    types = db.query(NoticeType).all()
    return types


@router.post("/notice-types")
async def create_notice_type(req: NoticeTypeCreate, db: Session = Depends(get_db)):
    new_type = NoticeType(**req.model_dump())
    db.add(new_type)
    db.commit()
    db.refresh(new_type)
    return new_type


@router.get("/gstr-summary/{period}")
async def gstr_summary(period: str, db: Session = Depends(get_db)):
    invoices = db.query(Invoice).filter(Invoice.status.in_(["approved", "paid"])).all()
    invoice_list = [
        {
            "subtotal": i.subtotal, "cgst": i.cgst,
            "sgst": i.sgst, "igst": i.igst,
            "buyer_gstin": None,
        }
        for i in invoices
    ]
    return await compliance_agent.generate_gstr_summary(invoice_list, period)
