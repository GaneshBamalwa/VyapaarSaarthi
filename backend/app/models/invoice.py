from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from app.database.session import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    order_id = Column(Integer, nullable=True)
    buyer_id = Column(Integer, nullable=True)
    buyer_name = Column(String(255), nullable=False)
    buyer_state = Column(String(100), nullable=False)
    line_items = Column(JSON, nullable=True)
    subtotal = Column(Float, default=0.0)
    cgst = Column(Float, default=0.0)
    sgst = Column(Float, default=0.0)
    igst = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    tax_type = Column(String(50), nullable=True)  # CGST+SGST or IGST
    status = Column(String(50), default="draft")  # draft, approved, paid, overdue
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Invoice id={self.id} number={self.invoice_number} status={self.status}>"
