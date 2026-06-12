import enum
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Enum, JSON, Text
from app.database.session import Base


class HITLStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EDITED = "EDITED"


class HITLQueue(Base):
    __tablename__ = "hitl_queue"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=True, index=True)
    graph_thread_id = Column(String(255), nullable=True)
    status = Column(Enum(HITLStatus), default=HITLStatus.PENDING)
    reason = Column(String(255), nullable=True)  # low_confidence, ambiguous
    payload = Column(JSON, nullable=False)
    edited_payload = Column(JSON, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<HITLQueue id={self.id} status={self.status} order_id={self.order_id}>"
