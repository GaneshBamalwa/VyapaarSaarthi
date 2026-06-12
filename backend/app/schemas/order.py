from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.order import OrderStatus


class OrderItemSchema(BaseModel):
    name: str
    quantity: Optional[int] = None
    unit: Optional[str] = None
    price: Optional[float] = None


class OrderItemResponse(OrderItemSchema):
    id: int
    order_id: int

    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    customer: Optional[str] = None
    raw_input: str
    input_type: str = "text"
    items: list[OrderItemSchema] = []
    delivery_date: Optional[str] = None
    confidence: Optional[float] = None
    notes: Optional[str] = None


class OrderUpdate(BaseModel):
    customer: Optional[str] = None
    status: Optional[OrderStatus] = None
    delivery_date: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    customer: Optional[str] = None
    raw_input: str
    input_type: str
    status: OrderStatus
    confidence: Optional[float] = None
    delivery_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemResponse] = []

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    total: int
    orders: list[OrderResponse]
