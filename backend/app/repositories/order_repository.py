from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: OrderCreate) -> Order:
        order = Order(
            customer=data.customer,
            raw_input=data.raw_input,
            input_type=data.input_type,
            status=OrderStatus.PENDING,
            confidence=data.confidence,
            delivery_date=data.delivery_date,
            notes=data.notes,
        )
        self.db.add(order)
        self.db.flush()

        for item_data in data.items:
            item = OrderItem(
                order_id=order.id,
                name=item_data.name,
                quantity=item_data.quantity,
                unit=item_data.unit,
                price=item_data.price,
            )
            self.db.add(item)

        self.db.commit()
        self.db.refresh(order)
        return order

    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self.db.query(Order).filter(Order.id == order_id).first()

    def list_all(self, month: Optional[str] = None, skip: int = 0, limit: int = 50) -> tuple[list[Order], int]:
        query = self.db.query(Order)
        if month:
            query = query.filter(Order.created_at.like(f"{month}-%"))
        total = query.count()
        orders = (
            query
            .order_by(desc(Order.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return orders, total

    def update_status(self, order_id: int, status: OrderStatus) -> Optional[Order]:
        order = self.get_by_id(order_id)
        if order:
            order.status = status
            self.db.commit()
            self.db.refresh(order)
        return order

    def count_by_status(self) -> dict[str, int]:
        from sqlalchemy import func
        results = (
            self.db.query(Order.status, func.count(Order.id))
            .group_by(Order.status)
            .all()
        )
        return {status.value: count for status, count in results}
