import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Float, Text
from sqlalchemy.orm import relationship
from app.database.session import Base


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer = Column(String(255), nullable=True)
    customer_phone = Column(String(20), nullable=True)  # captured from WhatsApp sender
    telegram_chat_id = Column(String(50), nullable=True) # captured from Telegram sender
    raw_input = Column(Text, nullable=False)
    input_type = Column(String(50), default="text")  # text, voice, image
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    payment_status = Column(String(50), default="PENDING")
    confidence = Column(Float, nullable=True)
    delivery_date = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order id={self.id} customer={self.customer} status={self.status}>"


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=True)
    unit = Column(String(50), nullable=True)
    price = Column(Float, nullable=True)

    order = relationship("Order", back_populates="items")

    def __repr__(self) -> str:
        return f"<OrderItem id={self.id} name={self.name} qty={self.quantity}>"
