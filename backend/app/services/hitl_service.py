from sqlalchemy.orm import Session
from datetime import datetime
from app.models.hitl_queue import HITLStatus
from app.models.order import OrderStatus
from app.repositories.hitl_repository import HITLRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.hitl import HITLResolveRequest
from app.websocket.manager import manager
from app.graph.main_graph import compiled_graph
from app.core.logging import get_logger

logger = get_logger(__name__)


class HITLService:
    def __init__(self, db: Session):
        self.hitl_repo = HITLRepository(db)
        self.order_repo = OrderRepository(db)

    def get_pending(self) -> list:
        return self.hitl_repo.list_pending()

    def get_all(self, limit: int = 50):
        return self.hitl_repo.list_all(limit=limit)

    async def resolve(self, hitl_id: int, request: HITLResolveRequest) -> dict:
        item = self.hitl_repo.get_by_id(hitl_id)
        if not item:
            return {"status": "error", "error": "HITL item not found"}

        if item.status != HITLStatus.PENDING:
            return {"status": "error", "error": "HITL item already resolved"}

        action_map = {
            "approve": HITLStatus.APPROVED,
            "reject": HITLStatus.REJECTED,
            "edit": HITLStatus.EDITED,
        }
        new_status = action_map.get(request.action, HITLStatus.APPROVED)

        resolved = self.hitl_repo.resolve(
            hitl_id=hitl_id,
            status=new_status,
            edited_payload=request.edited_payload,
            reviewer_notes=request.reviewer_notes,
        )

        # Update order status based on decision
        if item.order_id:
            order_status = (
                OrderStatus.APPROVED
                if request.action in ["approve", "edit"]
                else OrderStatus.REJECTED
            )
            self.order_repo.update_status(item.order_id, order_status)
            await manager.emit_order_event(item.order_id, order_status.value)

        # Resume LangGraph if thread exists
        if item.graph_thread_id and request.action in ["approve", "edit"]:
            await self._resume_graph(item.graph_thread_id, request)

        await manager.emit_hitl_event(hitl_id, new_status.value, {"action": request.action})

        return {"status": "success", "hitl_id": hitl_id, "new_status": new_status.value}

    async def _resume_graph(self, thread_id: str, request: HITLResolveRequest) -> None:
        """Resume a paused LangGraph after HITL approval."""
        try:
            config = {"configurable": {"thread_id": thread_id}}
            resume_input = {
                "hitl_approved": request.action in ["approve", "edit"],
                "hitl_edited_payload": request.edited_payload,
            }
            await compiled_graph.ainvoke(resume_input, config=config)
            logger.info(f"Graph resumed for thread {thread_id}")
        except Exception as e:
            logger.error(f"Failed to resume graph for thread {thread_id}: {e}")
