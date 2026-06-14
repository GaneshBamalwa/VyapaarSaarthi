from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database.session import Base


class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    nickname = Column(String(255), nullable=True)
    gstin = Column(String(50), nullable=True)
    state = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    telegram_chat_id = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    risk_tier = Column(String(50), default="Low")  # Low, Medium, High
    total_outstanding = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Buyer id={self.id} name={self.name} risk={self.risk_tier}>"
