from sqlalchemy.orm import Session
from app.communication.schemas import CommunicationRequest, CommunicationResponse, IntentParseResult
from app.communication.intents import IntentType
from app.communication.parser import get_intent_parser
from app.services.intake_service import IntakeService
from app.repositories.order_repository import OrderRepository
from app.models.order import OrderStatus
import logging

logger = logging.getLogger(__name__)

class CommunicationService:
    def __init__(self, db: Session):
        self.db = db
        self.parser = get_intent_parser()

    async def process_message(self, request: CommunicationRequest) -> CommunicationResponse:
        logger.info(f"Processing message from {request.user_id}: {request.message_text}")
        
        parsed = self.parser.parse(request.message_text)
        logger.info(f"Detected intent: {parsed.intent.value} with entities: {parsed.entities}")

        try:
            return await self._route_intent(parsed, request)
        except Exception as e:
            logger.error(f"Error processing intent {parsed.intent.value}: {str(e)}")
            return CommunicationResponse(
                intent=parsed.intent,
                success=False,
                message=f"Error processing request: {str(e)}"
            )

    async def _route_intent(self, parsed: IntentParseResult, request: CommunicationRequest) -> CommunicationResponse:
        if parsed.intent == IntentType.CREATE_ORDER:
            # Reuse IntakeService
            intake = IntakeService(self.db)
            raw_text = parsed.entities.get("raw_text", request.message_text)
            result = await intake.process_text_order(raw_text)
            return CommunicationResponse(
                intent=parsed.intent,
                success=True,
                data=result,
                message="Order Created successfully."
            )
            
        elif parsed.intent == IntentType.MARK_COMPLETED:
            order_id = parsed.entities.get("order_id")
            if not order_id:
                return CommunicationResponse(intent=parsed.intent, success=False, message="Order ID missing.")
            
            repo = OrderRepository(self.db)
            order = repo.update_status(order_id, OrderStatus.COMPLETED)
            if order:
                return CommunicationResponse(
                    intent=parsed.intent, 
                    success=True, 
                    data={"order_id": order.id},
                    message=f"Order ORD-{order.id} marked as completed."
                )
            return CommunicationResponse(intent=parsed.intent, success=False, message=f"Order ORD-{order_id} not found.")

        elif parsed.intent == IntentType.UPDATE_DELIVERY_DATE:
            order_id = parsed.entities.get("order_id")
            date_str = parsed.entities.get("delivery_date")
            if not order_id or not date_str:
                return CommunicationResponse(intent=parsed.intent, success=False, message="Order ID or Date missing.")
                
            repo = OrderRepository(self.db)
            order = repo.get_by_id(order_id)
            if order:
                order.delivery_date = date_str
                self.db.commit()
                return CommunicationResponse(
                    intent=parsed.intent,
                    success=True,
                    data={"order_id": order.id, "delivery_date": date_str},
                    message=f"Order ORD-{order.id} delivery updated to {date_str}."
                )
            return CommunicationResponse(intent=parsed.intent, success=False, message=f"Order ORD-{order_id} not found.")

        elif parsed.intent in [IntentType.LIST_ORDERS, IntentType.VIEW_PENDING, IntentType.VIEW_TODAY, IntentType.VIEW_OVERDUE]:
            repo = OrderRepository(self.db)
            orders, _ = repo.list_all(limit=20)
            
            if parsed.intent == IntentType.VIEW_PENDING:
                orders = [o for o in orders if o.status == OrderStatus.PENDING]
            
            # Simple dump for now
            data = [{"id": o.id, "customer": o.customer, "status": o.status.value, "date": o.delivery_date} for o in orders]
            return CommunicationResponse(
                intent=parsed.intent,
                success=True,
                data={"orders": data},
                message=f"Found {len(data)} orders."
            )

        elif parsed.intent == IntentType.SEARCH_ORDER:
            order_id = parsed.entities.get("order_id")
            repo = OrderRepository(self.db)
            if order_id:
                order = repo.get_by_id(order_id)
                data = [{"id": order.id, "customer": order.customer, "status": order.status.value, "date": order.delivery_date}] if order else []
                return CommunicationResponse(
                    intent=parsed.intent,
                    success=True,
                    data={"orders": data},
                    message=f"Found {len(data)} orders." if data else "Order not found."
                )

        return CommunicationResponse(
            intent=parsed.intent,
            success=False,
            message="Sorry, I could not understand the request."
        )
