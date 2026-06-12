import uuid
from sqlalchemy.orm import Session
from app.agents.intake import IntakeAgent, IntakeInput
from app.agents.clarification import ClarificationAgent
from app.repositories.order_repository import OrderRepository
from app.repositories.hitl_repository import HITLRepository
from app.schemas.order import OrderCreate, OrderItemSchema
from app.models.hitl_queue import HITLStatus
from app.models.order import OrderStatus
from app.graph.main_graph import compiled_graph
from app.websocket.manager import manager
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_intake_agent = IntakeAgent()
_clarification_agent = ClarificationAgent()


class IntakeService:
    def __init__(self, db: Session):
        self.order_repo = OrderRepository(db)
        self.hitl_repo = HITLRepository(db)

    async def process_text_order(self, raw_text: str) -> dict:
        """Parse text order, check ambiguity, create order, and queue HITL if needed."""

        # Step 1: Clarification check
        clarification = await _clarification_agent.invoke({"text": raw_text})
        is_ambiguous = (
            clarification.get("status") == "success"
            and clarification["data"].get("status") == "AMBIGUOUS"
        )

        # Step 2: Parse with intake agent
        intake_result = await _intake_agent.invoke(IntakeInput(text=raw_text))

        if intake_result["status"] != "success":
            return {"status": "error", "error": intake_result.get("error")}

        parsed = intake_result["data"]
        confidence = parsed.get("confidence", 0.0)

        # Step 3: Create order
        order_data = OrderCreate(
            raw_input=raw_text,
            input_type="text",
            customer=parsed.get("customer"),
            items=[OrderItemSchema(**i) for i in parsed.get("items", [])],
            delivery_date=parsed.get("delivery_date"),
            confidence=confidence,
            notes=parsed.get("notes"),
        )
        order = self.order_repo.create(order_data)

        # Step 4: Check if HITL needed
        requires_hitl = confidence < settings.HITL_CONFIDENCE_THRESHOLD or is_ambiguous
        hitl_item = None

        if requires_hitl:
            reason = "ambiguous" if is_ambiguous else "low_confidence"
            hitl_payload = {
                "raw_input": raw_text,
                "parsed_order": parsed,
                "clarification": clarification.get("data"),
                "confidence": confidence,
            }
            hitl_item = self.hitl_repo.create(
                payload=hitl_payload,
                order_id=order.id,
                reason=reason,
            )
            self.order_repo.update_status(order.id, OrderStatus.AWAITING_APPROVAL)
            await manager.emit_hitl_event(hitl_item.id, "created", hitl_payload)

        await manager.emit_order_event(order.id, order.status.value, {"customer": order.customer})

        return {
            "status": "success",
            "order_id": order.id,
            "parsed": parsed,
            "requires_hitl": requires_hitl,
            "hitl_id": hitl_item.id if hitl_item else None,
            "clarification": clarification.get("data"),
        }

    async def run_graph_pipeline(self, raw_text: str, input_type: str = "text") -> dict:
        """Run the full LangGraph pipeline."""
        thread_id = str(uuid.uuid4())

        initial_state = {
            "raw_input": raw_text,
            "input_type": input_type,
            "thread_id": thread_id,
            "requires_hitl": False,
            "messages": [],
        }

        config = {"configurable": {"thread_id": thread_id}}

        try:
            result = await compiled_graph.ainvoke(initial_state, config=config)
            return {"status": "success", "thread_id": thread_id, "result": result}
        except Exception as e:
            logger.error(f"Graph pipeline error: {e}")
            return {"status": "error", "error": str(e), "thread_id": thread_id}
