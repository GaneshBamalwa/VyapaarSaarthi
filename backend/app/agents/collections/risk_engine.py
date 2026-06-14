from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.logging import get_logger

logger = get_logger(__name__)


def calculate_risk_tier(payment_history: list[dict]) -> str:
    """
    payment_history: list of dicts with keys:
      delay_days (int), amount (float), paid_at (datetime)
    Returns: 'low' | 'medium' | 'high'
    """
    if not payment_history:
        return "low"

    total = len(payment_history)
    avg_delay = sum(p["delay_days"] for p in payment_history) / total
    overdue_count = sum(1 for p in payment_history if p["delay_days"] > 0)
    overdue_ratio = overdue_count / total

    # Weight recent behaviour more heavily (last 5 payments)
    recent = sorted(
        payment_history,
        key=lambda x: x.get("paid_at") or datetime.min,
        reverse=True,
    )[:5]
    recent_avg = sum(p["delay_days"] for p in recent) / len(recent)

    score = 0
    if avg_delay > 15:
        score += 3
    elif avg_delay > 7:
        score += 2
    elif avg_delay > 0:
        score += 1

    if overdue_ratio > 0.6:
        score += 3
    elif overdue_ratio > 0.3:
        score += 2
    elif overdue_ratio > 0:
        score += 1

    if recent_avg > 10:
        score += 2
    elif recent_avg > 5:
        score += 1

    if score >= 6:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def format_inr(amount: float) -> str:
    """
    Formats float as Indian number system string.
    1000      → "1,000"
    100000    → "1,00,000"
    10000000  → "1,00,00,000"
    """
    amount = int(round(amount))
    s = str(amount)
    if len(s) <= 3:
        return s
    result = s[-3:]
    s = s[:-3]
    while s:
        result = s[-2:] + "," + result
        s = s[:-2]
    return result.lstrip(",")


def update_all_risk_scores(db: Session) -> int:
    """
    Reads all invoices, groups by buyer, calculates risk,
    upserts into buyer_risk_profiles. Returns count updated.
    Uses Invoice model which has buyer_name, due_date, total, status fields.
    """
    from app.models.invoice import Invoice
    from app.models.collections import BuyerRiskProfile

    today = date.today()

    # Fetch all invoices that are not drafts
    invoices = db.query(Invoice).filter(Invoice.status != "draft").all()

    # Group by buyer_name
    buyer_map: dict[str, list[dict]] = {}
    for inv in invoices:
        buyer = inv.buyer_name or "Unknown"
        if buyer not in buyer_map:
            buyer_map[buyer] = []

        # Calculate delay: positive = days late, 0 = on time
        if inv.due_date:
            if inv.status in ("paid",):
                # For paid invoices, use due_date vs a proxy "paid at" = updated/created
                # We use created_at as a conservative proxy since we don't track paid_at
                paid_proxy = inv.created_at if inv.created_at else datetime.utcnow()
                delay = max(0, (paid_proxy.date() - inv.due_date.date()).days)
            else:
                # Unpaid/overdue: compare due_date vs today
                delay = max(0, (today - inv.due_date.date()).days)
        else:
            delay = 0

        buyer_map[buyer].append(
            {
                "delay_days": delay,
                "amount": float(inv.total or 0.0),
                "paid_at": inv.created_at or datetime.utcnow(),
            }
        )

    count = 0
    for buyer_name, history in buyer_map.items():
        if not buyer_name or buyer_name == "Unknown":
            continue

        tier = calculate_risk_tier(history)
        total_payments = len(history)
        avg_delay = sum(p["delay_days"] for p in history) / total_payments if total_payments else 0.0
        overdue_count = sum(1 for p in history if p["delay_days"] > 0)
        overdue_ratio = overdue_count / total_payments if total_payments else 0.0
        total_overdue_amt = sum(
            p["amount"] for p in history if p["delay_days"] > 0
        )

        # Upsert
        profile = db.query(BuyerRiskProfile).filter(
            BuyerRiskProfile.buyer_name == buyer_name
        ).first()

        if profile:
            profile.risk_tier = tier
            profile.avg_delay_days = round(avg_delay, 2)
            profile.overdue_ratio = round(overdue_ratio, 4)
            profile.total_overdue_amt = round(total_overdue_amt, 2)
            profile.payment_count = total_payments
            profile.last_updated = datetime.utcnow()
        else:
            profile = BuyerRiskProfile(
                buyer_name=buyer_name,
                risk_tier=tier,
                avg_delay_days=round(avg_delay, 2),
                overdue_ratio=round(overdue_ratio, 4),
                total_overdue_amt=round(total_overdue_amt, 2),
                payment_count=total_payments,
            )
            db.add(profile)

        count += 1

    try:
        db.commit()
    except Exception as e:
        logger.error(f"Risk score upsert failed: {e}")
        db.rollback()

    return count
