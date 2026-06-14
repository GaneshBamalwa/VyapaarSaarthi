from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from app.database.session import Base


class BuyerRiskProfile(Base):
    __tablename__ = "buyer_risk_profiles"

    id = Column(Integer, primary_key=True, index=True)
    buyer_name = Column(String(255), nullable=False, unique=True, index=True)
    buyer_phone = Column(String(20), nullable=True)
    risk_tier = Column(String(20), nullable=False, default="low")
    avg_delay_days = Column(Float, nullable=False, default=0.0)
    overdue_ratio = Column(Float, nullable=False, default=0.0)
    total_overdue_amt = Column(Float, nullable=False, default=0.0)
    payment_count = Column(Integer, nullable=False, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<BuyerRiskProfile buyer={self.buyer_name} tier={self.risk_tier}>"


class CollectionReminder(Base):
    __tablename__ = "collection_reminders"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, nullable=True)           # soft ref, no FK constraint
    buyer_name = Column(String(255), nullable=False, index=True)
    buyer_phone = Column(String(20), nullable=True)
    amount_due = Column(Float, nullable=False)
    days_overdue = Column(Integer, nullable=False)
    level = Column(Integer, nullable=False)               # 1=polite, 2=firm
    message_text = Column(Text, nullable=False)
    status = Column(String(30), nullable=False, default="sent")
    # 'sent' | 'failed' | 'pending_hitl' | 'approved' | 'rejected'
    whatsapp_sid = Column(String(100), nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<CollectionReminder id={self.id} buyer={self.buyer_name} "
            f"level={self.level} status={self.status}>"
        )
