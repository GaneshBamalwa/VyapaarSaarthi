from sqlalchemy.orm import Session
from app.communication.schemas import CommunicationRequest, CommunicationResponse, IntentParseResult
from app.communication.intents import IntentType
from app.communication.parser import get_intent_parser
from app.services.intake_service import IntakeService
from app.repositories.order_repository import OrderRepository
from app.models.order import OrderStatus
from app.models.buyer import Buyer
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

            # Save phone number or telegram chat ID
            phone = request.phone_number
            telegram_id = request.user_id if request.channel == "telegram" else None
            
            if (phone or telegram_id) and result.get("status") == "success" and result.get("order_id"):
                self._save_contact_to_order_and_buyer(
                    order_id=result["order_id"],
                    buyer_name=result.get("parsed", {}).get("customer"),
                    phone=phone,
                    telegram_chat_id=telegram_id
                )

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
                if order.status == OrderStatus.COMPLETED:
                    return CommunicationResponse(
                        intent=parsed.intent, 
                        success=False, 
                        message=f"Order ORD-{order.id} is already completed and cannot be modified."
                    )
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
            elif parsed.intent == IntentType.VIEW_OVERDUE:
                from datetime import datetime
                today = datetime.utcnow().strftime("%Y-%m-%d")
                orders = [o for o in orders if o.delivery_date and o.delivery_date < today and o.status != OrderStatus.COMPLETED]
            elif parsed.intent == IntentType.VIEW_TODAY:
                from datetime import datetime
                today = datetime.utcnow().strftime("%Y-%m-%d")
                orders = [o for o in orders if o.delivery_date == today]
            
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

        elif parsed.intent == IntentType.GENERATE_INVOICE:
            repo = OrderRepository(self.db)
            order_id = parsed.entities.get("order_id")
            customer = parsed.entities.get("customer")
            
            if order_id:
                order = repo.get_by_id(order_id)
                if order:
                    return CommunicationResponse(
                        intent=parsed.intent,
                        success=True,
                        data={"invoice_order_id": order.id, "customer": order.customer},
                        message=f"Generating invoice for Order {order.id}"
                    )
            
            if customer:
                from app.models.order import Order
                orders = self.db.query(Order).filter(Order.status.notin_(["REJECTED", "CANCELLED", "draft"]), Order.customer.ilike(f"%{customer}%")).order_by(Order.created_at.desc()).limit(1).all()
                if orders:
                    return CommunicationResponse(
                        intent=parsed.intent,
                        success=True,
                        data={"invoice_order_id": orders[0].id, "customer": orders[0].customer},
                        message=f"Generating invoice for Order {orders[0].id} ({orders[0].customer})"
                    )

            # Return list of recent orders for selection
            from app.models.order import Order
            orders = self.db.query(Order).filter(Order.status.notin_(["REJECTED", "CANCELLED", "draft"])).order_by(Order.created_at.desc()).limit(10).all()
            if not orders:
                return CommunicationResponse(intent=parsed.intent, success=False, message="No recent orders found to invoice.")
            
            data = [{"id": o.id, "customer": o.customer, "status": o.status.value, "date": o.delivery_date} for o in orders]
            return CommunicationResponse(
                intent=parsed.intent,
                success=True,
                data={"needs_invoice_selection": True, "orders": data},
                message="Please select an order for the invoice:"
            )

        elif parsed.intent == IntentType.DOWNLOAD_EXCEL:
            from app.routers.expenses import generate_report_excel
            import datetime
            target_month = datetime.datetime.utcnow().strftime("%Y-%m")
            report_type = parsed.entities.get("report_type", "both")
            
            try:
                buffer = generate_report_excel(self.db, target_month, report_type)
                return CommunicationResponse(
                    intent=parsed.intent,
                    success=True,
                    data={"excel_bytes": buffer.getvalue(), "report_type": report_type, "target_month": target_month},
                    message=f"Generating {report_type} excel sheet for {target_month}..."
                )
            except Exception as e:
                logger.error(f"Failed to generate excel: {e}")
                return CommunicationResponse(
                    intent=parsed.intent,
                    success=False,
                    message="Failed to generate the excel sheet."
                )

        return CommunicationResponse(
            intent=parsed.intent,
            success=False,
            message="Sorry, I could not understand the request."
        )

    def _save_contact_to_order_and_buyer(
        self, order_id: int, buyer_name: str | None, phone: str | None, telegram_chat_id: str | None
    ) -> None:
        """
        Saves the contact info to:
          1. order.customer_phone and/or order.telegram_chat_id
          2. buyers.phone and/or buyers.telegram_chat_id
        """
        try:
            from app.models.order import Order
            order = self.db.query(Order).filter(Order.id == order_id).first()
            if order:
                changed = False
                if phone and not order.customer_phone:
                    order.customer_phone = phone
                    changed = True
                if telegram_chat_id and not order.telegram_chat_id:
                    order.telegram_chat_id = telegram_chat_id
                    changed = True
                if changed:
                    self.db.commit()
                    logger.info(f"Saved contact to order #{order_id}")
        except Exception as e:
            logger.error(f"Failed to save contact to order #{order_id}: {e}")

        if not buyer_name:
            return
        try:
            existing = self.db.query(Buyer).filter(Buyer.name == buyer_name).first()
            if existing:
                changed = False
                if phone and not existing.phone:
                    existing.phone = phone
                    changed = True
                if telegram_chat_id and not existing.telegram_chat_id:
                    existing.telegram_chat_id = telegram_chat_id
                    changed = True
                if changed:
                    self.db.commit()
            else:
                buyer = Buyer(name=buyer_name, phone=phone, telegram_chat_id=telegram_chat_id)
                self.db.add(buyer)
                self.db.commit()
        except Exception as e:
            logger.error(f"Failed to save contact to buyer '{buyer_name}': {e}")
