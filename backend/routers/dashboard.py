from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from database import get_db, Invoice, Buyer, HITLQueue, OrderHITLQueue, Order

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    weekly_revenue = db.query(func.sum(Invoice.total)).filter(
        Invoice.status.in_(["paid", "approved"]),
        Invoice.created_at >= week_ago,
    ).scalar() or 0

    recovered_this_week = db.query(func.sum(Invoice.total)).filter(
        Invoice.status == "paid",
        Invoice.created_at >= week_ago,
    ).scalar() or 0

    outstanding = db.query(func.sum(Invoice.total)).filter(
        Invoice.status == "overdue"
    ).scalar() or 0

    overdue_count = db.query(func.count(Invoice.id)).filter(
        Invoice.status == "overdue"
    ).scalar() or 0

    # Pending approvals across both HITL queues
    gst_pending = db.query(func.count(HITLQueue.id)).filter(
        HITLQueue.status == "pending"
    ).scalar() or 0
    intake_pending = db.query(func.count(OrderHITLQueue.id)).filter(
        OrderHITLQueue.status == "PENDING"
    ).scalar() or 0

    buyers_at_risk = db.query(func.count(Buyer.id)).filter(
        Buyer.risk_tier == "High"
    ).scalar() or 0

    total_invoices = db.query(func.count(Invoice.id)).scalar() or 0
    total_buyers = db.query(func.count(Buyer.id)).scalar() or 0

    return {
        "weekly_revenue": round(float(weekly_revenue), 2),
        "outstanding": round(float(outstanding), 2),
        "recovered_this_week": round(float(recovered_this_week), 2),
        "overdue_count": int(overdue_count),
        "pending_approvals": int(gst_pending + intake_pending),
        "buyers_at_risk": int(buyers_at_risk),
        "total_invoices": int(total_invoices),
        "total_buyers": int(total_buyers),
    }


@router.get("/cashflow")
def get_cashflow(db: Session = Depends(get_db)):
    """Monthly cash flow for last 6 months computed from real invoices."""
    now = datetime.utcnow()
    months = []
    for i in range(5, -1, -1):
        dt = now - timedelta(days=30 * i)
        months.append((dt.year, dt.month))

    result = []
    for year, month in months:
        start = datetime(year, month, 1)
        # end = first day of next month
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        income = db.query(func.sum(Invoice.total)).filter(
            Invoice.status.in_(["paid", "approved"]),
            Invoice.created_at >= start,
            Invoice.created_at < end,
        ).scalar() or 0

        # Estimate expenses as ~35% of revenue (no expense table yet)
        expense = round(float(income) * 0.35, 2)

        result.append({
            "month": start.strftime("%b"),
            "in": round(float(income), 2),
            "out": expense,
        })

    return result


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db)):
    """Live alert feed from DB state."""
    alerts = []
    now = datetime.utcnow()

    overdue = db.query(Invoice).filter(Invoice.status == "overdue").all()
    for inv in overdue:
        days = (now - inv.due_date).days if inv.due_date else 0
        alerts.append({
            "type": "overdue",
            "severity": "high" if days > 30 else "medium",
            "message": f"{inv.buyer_name} — ₹{inv.total:,.0f} overdue by {days} days",
            "invoice_number": inv.invoice_number,
        })

    gst_pending = db.query(HITLQueue).filter(HITLQueue.status == "pending").count()
    intake_pending = db.query(OrderHITLQueue).filter(OrderHITLQueue.status == "PENDING").count()
    if gst_pending + intake_pending > 0:
        alerts.append({
            "type": "approval",
            "severity": "medium",
            "message": f"{gst_pending + intake_pending} items waiting for your approval",
        })

    # GST deadline alert
    day = now.day
    if day <= 11:
        alerts.append({"type": "gst", "severity": "low", "message": f"GSTR-1 due on {now.year}-{now.month:02d}-11"})
    elif day <= 20:
        alerts.append({"type": "gst", "severity": "medium", "message": f"GSTR-3B due on {now.year}-{now.month:02d}-20"})

    return alerts
