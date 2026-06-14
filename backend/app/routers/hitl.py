from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.hitl_service import HITLService
from app.schemas.hitl import HITLListResponse, HITLResolveRequest, HITLQueueResponse
from app.models.collections import CollectionReminder
from app.agents.collections.risk_engine import format_inr

router = APIRouter(prefix="/api/hitl", tags=["HITL"])


@router.get("/pending")
async def get_pending(db: Session = Depends(get_db)):
    service = HITLService(db)
    order_items = service.get_pending()
    items = [HITLQueueResponse.model_validate(i) for i in order_items]

    # Merge pending collection reminders into the HITL list
    pending_reminders = (
        db.query(CollectionReminder)
        .filter(CollectionReminder.status == "pending_hitl")
        .all()
    )
    for reminder in pending_reminders:
        items.append({
            "id": reminder.id,
            "type": "collection_reminder",
            "title": f"Payment reminder — {reminder.buyer_name}",
            "subtitle": (
                f"₹{format_inr(reminder.amount_due)} overdue {reminder.days_overdue} days"
                f" · Level {reminder.level} · High Risk"
            ),
            "created_at": reminder.sent_at,
            "action_endpoint": "/api/collections/hitl/approve",
            "order_id": None,
            "graph_thread_id": None,
            "status": "PENDING",
            "reason": "high_risk_level2",
            "payload": {
                "buyer_name": reminder.buyer_name,
                "amount_due": reminder.amount_due,
                "days_overdue": reminder.days_overdue,
                "level": reminder.level,
            },
            "edited_payload": None,
            "reviewer_notes": None,
            "resolved_at": None,
        })

    return {"total": len(items), "items": items}


@router.get("/all")
async def get_all(limit: int = 50, db: Session = Depends(get_db)):
    service = HITLService(db)
    items, total = service.get_all(limit=limit)
    return HITLListResponse(
        total=total,
        items=[HITLQueueResponse.model_validate(i) for i in items]
    )


@router.post("/{hitl_id}/resolve")
async def resolve_hitl(
    hitl_id: int,
    body: HITLResolveRequest,
    db: Session = Depends(get_db),
):
    if body.action not in ["approve", "reject", "edit"]:
        raise HTTPException(status_code=400, detail="Action must be approve, reject, or edit")

    service = HITLService(db)
    result = await service.resolve(hitl_id, body)

    if result["status"] == "error":
        raise HTTPException(status_code=404, detail=result["error"])

    return result
