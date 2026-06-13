from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, JSON, Boolean, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vyapaar_mvp.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SellerProfile(Base):
    __tablename__ = "seller_profiles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, default="Sharma Steel Pvt Ltd")
    gstin = Column(String, default="27AAPFU0939F1ZV")
    state = Column(String, default="Maharashtra")
    address = Column(String, default="Plot 45, MIDC Industrial Area, Pune - 411018")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MSMEScheme(Base):
    __tablename__ = "msme_schemes"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    min_turnover = Column(Float)
    max_turnover = Column(Float)
    benefit = Column(Text)
    eligibility = Column(Text)
    apply_url = Column(String)


class NoticeType(Base):
    __tablename__ = "notice_types"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    description = Column(Text)
class Buyer(Base):
    __tablename__ = "buyers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    nickname = Column(String)
    gstin = Column(String)
    state = Column(String)
    phone = Column(String)
    email = Column(String)
    risk_tier = Column(String, default="Low")  # Low, Medium, High
    total_outstanding = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String, unique=True)
    order_id = Column(Integer)
    buyer_id = Column(Integer)
    buyer_name = Column(String)
    buyer_state = Column(String)
    line_items = Column(JSON)
    subtotal = Column(Float)
    cgst = Column(Float, default=0.0)
    sgst = Column(Float, default=0.0)
    igst = Column(Float, default=0.0)
    total = Column(Float)
    tax_type = Column(String)  # CGST+SGST or IGST
    status = Column(String, default="draft")  # draft, approved, paid, overdue
    due_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class HITLQueue(Base):
    __tablename__ = "hitl_queue"
    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String)  # invoice_draft, reminder, notice_response
    payload = Column(JSON)
    status = Column(String, default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


class AgentTrace(Base):
    __tablename__ = "agent_traces"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String)
    event_type = Column(String)
    message = Column(Text)
    trace_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GSTNotice(Base):
    __tablename__ = "gst_notices"
    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text)
    translated_hindi = Column(Text, nullable=True)
    action_items = Column(JSON, nullable=True)
    status = Column(String, default="unreviewed")
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String)  # user, assistant
    content = Column(Text)
    audio_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Order Intake Models (from VyapaarSaarthi integration) ──────────────────

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"


class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    customer = Column(String(255), nullable=True)
    raw_input = Column(Text, nullable=False)
    input_type = Column(String(50), default="text")  # text, voice, image
    status = Column(String(50), default="PENDING")
    confidence = Column(Float, nullable=True)
    delivery_date = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=True)
    unit = Column(String(50), nullable=True)
    price = Column(Float, nullable=True)
    order = relationship("Order", back_populates="items")


class OrderHITLQueue(Base):
    __tablename__ = "order_hitl_queue"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    graph_thread_id = Column(String(255), nullable=True)
    status = Column(String(50), default="PENDING")  # PENDING, APPROVED, REJECTED, EDITED
    reason = Column(String(255), nullable=True)      # ambiguous, low_confidence
    payload = Column(JSON, nullable=True)
    edited_payload = Column(JSON, nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)
    seed_db()


def seed_db():
    db = SessionLocal()
    try:
        # Seed Seller Profile
        if not db.query(SellerProfile).first():
            profile = SellerProfile()
            db.add(profile)
        
        # Seed Notice Types
        if not db.query(NoticeType).first():
            notices = [
                {"code": "ASMT-10", "description": "Scrutiny of Returns — department found discrepancy in your GST return"},
                {"code": "DRC-01", "description": "Demand Notice — tax, interest and penalty demand raised"},
                {"code": "DRC-03", "description": "Voluntary Payment — you can pay tax/interest/penalty voluntarily"},
                {"code": "REG-03", "description": "Notice for additional information on registration application"},
                {"code": "GSTR-3A", "description": "Default Notice — GSTR-3B not filed within due date"},
            ]
            for n in notices:
                db.add(NoticeType(**n))
                
        # Seed MSME Schemes
        if not db.query(MSMEScheme).first():
            schemes = [
                {
                    "name": "MUDRA Kishore Loan",
                    "min_turnover": 0,
                    "max_turnover": 5000000,
                    "benefit": "Loan up to ₹5L at 8.5% PA, no collateral",
                    "eligibility": "Annual turnover < ₹50L, operating 2+ years",
                    "apply_url": "mudra.org.in",
                },
                {
                    "name": "CGTMSE Credit Guarantee",
                    "min_turnover": 500000,
                    "max_turnover": 100000000,
                    "benefit": "Credit guarantee up to ₹25L — no third-party collateral needed",
                    "eligibility": "Manufacturing or service MSMEs registered under MSMED Act",
                    "apply_url": "cgtmse.in",
                },
                {
                    "name": "PM Vishwakarma Scheme",
                    "min_turnover": 0,
                    "max_turnover": 1500000,
                    "benefit": "₹3L collateral-free credit, skill training, digital payments incentive",
                    "eligibility": "Traditional artisans and craftspeople, turnover < ₹15L",
                    "apply_url": "pmvishwakarma.gov.in",
                },
                {
                    "name": "TReDS Invoice Financing",
                    "min_turnover": 1000000,
                    "max_turnover": 500000000,
                    "benefit": "Early payment against trade receivables at competitive rates",
                    "eligibility": "MSME supplier to corporates, registered on TReDS platform",
                    "apply_url": "treds.in",
                },
                {
                    "name": "GeM Seller Registration",
                    "min_turnover": 0,
                    "max_turnover": 100000000,
                    "benefit": "Sell directly to government departments — guaranteed payment in 10 days",
                    "eligibility": "Any registered MSME with Udyam Registration",
                    "apply_url": "gem.gov.in",
                },
            ]
            for s in schemes:
                db.add(MSMEScheme(**s))
                
        db.commit()
    finally:
        db.close()
