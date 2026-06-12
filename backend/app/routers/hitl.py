from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.hitl_service import HITLService
from app.schemas.hitl import HITLListResponse, HITLResolveRequest, HITLQueueResponse

router = APIRouter(prefix="/api/hitl", tags=["HITL"])


@router.get("/pending")
async def get_pending(db: Session = Depends(get_db)):
    service = HITLService(db)
    items = service.get_pending()
    return {"total": len(items), "items": [HITLQueueResponse.model_validate(i) for i in items]}


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
