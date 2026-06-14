from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from app.database.session import Base

class ExpenseEntry(Base):
    __tablename__ = "expense_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    vendor_name = Column(Text, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(Text, default="INR")
    is_paid = Column(Boolean, default=False)
    due_date = Column(Text, nullable=True)
    paid_on = Column(Text, nullable=True)
    linked_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    receipt_ref = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(Text, server_default=func.current_timestamp())

class MonthlyReportMeta(Base):
    __tablename__ = "monthly_report_meta"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(Text, unique=True, nullable=False)
    report_generated_at = Column(Text, nullable=True)
    orders_total = Column(Float, nullable=True)
    expenses_total = Column(Float, nullable=True)
    net_position = Column(Float, nullable=True)
    is_closed = Column(Boolean, default=False)
