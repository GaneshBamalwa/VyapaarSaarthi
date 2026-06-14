from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class ExpenseCategory(str, Enum):
    RENT = "RENT"
    ELECTRICITY = "ELECTRICITY"
    GST_TAX = "GST_TAX"
    RAW_MATERIAL = "RAW_MATERIAL"
    DELIVERY = "DELIVERY"
    SALARY = "SALARY"
    MISCELLANEOUS = "MISCELLANEOUS"

class ExpenseCreateSchema(BaseModel):
    category: ExpenseCategory
    description: str
    vendor_name: Optional[str] = None
    amount: float
    due_date: Optional[str] = None
    linked_order_id: Optional[int] = None
    receipt_ref: Optional[str] = None

class ExpenseResponseSchema(ExpenseCreateSchema):
    id: int
    month: str
    currency: str
    is_paid: bool
    paid_on: Optional[str] = None
    created_at: str
    is_deleted: bool

    class Config:
        from_attributes = True

class CategoryBreakdownSchema(BaseModel):
    category: str
    amount: float

class MonthlyReportSchema(BaseModel):
    month: str
    orders_total: float
    expenses_total: float
    net_position: float
    is_closed: bool
    category_breakdown: List[CategoryBreakdownSchema]
