from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.intake_service import IntakeService
from app.repositories.order_repository import OrderRepository
from app.schemas.order import OrderListResponse, OrderResponse

router = APIRouter(prefix="/api", tags=["Intake & Orders"])


class IntakeRequest(BaseModel):
    text: str


@router.post("/intake")
async def process_intake(body: IntakeRequest, db: Session = Depends(get_db)):
    """Parse unstructured order text and create an order."""
    service = IntakeService(db)
    result = await service.process_text_order(body.text)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    repo = OrderRepository(db)
    orders, total = repo.list_all(skip=skip, limit=limit)
    return OrderListResponse(total=total, orders=orders)


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    repo = OrderRepository(db)
    order = repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/orders/{order_id}/fulfill")
async def fulfill_order(order_id: int, db: Session = Depends(get_db)):
    from app.models.order import OrderStatus
    from app.websocket.manager import manager
    repo = OrderRepository(db)
    order = repo.update_status(order_id, OrderStatus.COMPLETED)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    await manager.emit_order_event(order.id, order.status.value, {"customer": order.customer})
    return {"status": "success", "order_id": order.id}
