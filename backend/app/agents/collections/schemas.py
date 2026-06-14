from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class RiskTier(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ReminderLevel(int, Enum):
    LEVEL_1 = 1
    LEVEL_2 = 2


class ReminderStatus(str, Enum):
    SENT = "sent"
    FAILED = "failed"
    PENDING_HITL = "pending_hitl"
    APPROVED = "approved"
    REJECTED = "rejected"


class BuyerRiskProfileOut(BaseModel):
    buyer_name: str
    buyer_phone: Optional[str] = None
    risk_tier: RiskTier
    avg_delay_days: float
    overdue_ratio: float
    total_overdue_amt: float
    payment_count: int
    last_updated: datetime

    class Config:
        from_attributes = True


class CollectionReminderOut(BaseModel):
    id: int
    invoice_id: Optional[int] = None
    buyer_name: str
    buyer_phone: Optional[str] = None
    amount_due: float
    days_overdue: int
    level: int
    message_text: str
    status: ReminderStatus
    whatsapp_sid: Optional[str] = None
    sent_at: datetime

    class Config:
        from_attributes = True


class OverdueInvoiceOut(BaseModel):
    invoice_id: int
    buyer_name: str
    buyer_phone: Optional[str] = None
    has_phone: bool = False
    amount_due: float
    due_date: datetime
    days_overdue: int
    risk_tier: Optional[RiskTier] = None


class ManualReminderRequest(BaseModel):
    invoice_id: int
    override_level: Optional[int] = None  # 1 or 2


class HITLApprovalRequest(BaseModel):
    reminder_id: int
    approved: bool
    approved_by: str


class CollectionsStatsOut(BaseModel):
    total_overdue_invoices: int
    total_overdue_amount: float
    high_risk_buyers: int
    medium_risk_buyers: int
    low_risk_buyers: int
    reminders_sent_today: int
    reminders_pending_hitl: int
