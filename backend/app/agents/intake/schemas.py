from pydantic import BaseModel, Field
from typing import Optional


class IntakeItem(BaseModel):
    name: str
    quantity: Optional[int] = None
    unit: Optional[str] = None


class IntakeInput(BaseModel):
    text: str = Field(..., description="Raw order text in Hindi or English")


class IntakeOutput(BaseModel):
    customer: str = ""
    items: list[IntakeItem] = []
    delivery_date: str = ""
    confidence: float = 0.0
    notes: str = ""
