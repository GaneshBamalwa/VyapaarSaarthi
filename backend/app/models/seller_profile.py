from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.database.session import Base


class SellerProfile(Base):
    __tablename__ = "seller_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), default="Sharma Steel Pvt Ltd", nullable=False)
    gstin = Column(String(50), default="27AAPFU0939F1ZV", nullable=False)
    state = Column(String(100), default="Maharashtra", nullable=False)
    address = Column(String(512), default="Plot 45, MIDC Industrial Area, Pune - 411018", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<SellerProfile id={self.id} name={self.name}>"
