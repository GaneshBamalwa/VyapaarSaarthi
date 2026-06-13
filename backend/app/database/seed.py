"""Seed dummy data for development and demo."""
import random
from datetime import datetime, timedelta
from app.database.session import SessionLocal
from app.models import (
    Buyer, Invoice, GSTNotice, HITLQueue, AgentTrace,
    SellerProfile, MSMEScheme, NoticeType
)

DUMMY_BUYERS = [
    {"name": "Ramesh Traders", "nickname": "Ramesh bhai", "gstin": "29AABCT1332L1ZK", "state": "Karnataka", "phone": "9876543210", "email": "ramesh@traders.com", "risk_tier": "Low"},
    {"name": "Suresh Enterprises", "nickname": "Suresh ji", "gstin": "07AAACR5055K1Z5", "state": "Delhi", "phone": "9845678901", "email": "suresh@ent.com", "risk_tier": "High"},
    {"name": "Kaveri Steel Works", "nickname": "Kaveri", "gstin": "33AABCS1429B1Z0", "state": "Tamil Nadu", "phone": "9912345678", "email": "kaveri@steel.com", "risk_tier": "Medium"},
    {"name": "Patel Hardware", "nickname": "Patel sahab", "gstin": "24AAACC1206D1ZM", "state": "Gujarat", "phone": "9988776655", "email": "patel@hardware.com", "risk_tier": "Low"},
    {"name": "Local Shop (No GSTIN)", "nickname": "Corner wala", "gstin": None, "state": "Maharashtra", "phone": "9001234567", "email": None, "risk_tier": "Low"},
]

DUMMY_INVOICES = [
    {
        "invoice_number": "VYP/2024/0001",
        "order_id": 1,
        "buyer_id": 1,
        "buyer_name": "Ramesh Traders",
        "buyer_state": "Karnataka",
        "line_items": [
            {"name": "Steel Rods", "qty": 100, "unit": "kg", "rate": 85.0, "hsn": "7214", "gst_rate": 18, "taxable_value": 8500, "cgst": 0, "sgst": 0, "igst": 1530, "item_total": 10030},
        ],
        "subtotal": 8500.0,
        "cgst": 0.0,
        "sgst": 0.0,
        "igst": 1530.0,
        "total": 10030.0,
        "tax_type": "IGST",
        "status": "paid",
        "due_date": datetime.now() - timedelta(days=15),
    },
    {
        "invoice_number": "VYP/2024/0002",
        "order_id": 2,
        "buyer_id": 5,
        "buyer_name": "Local Shop (No GSTIN)",
        "buyer_state": "Maharashtra",
        "line_items": [
            {"name": "Iron Sheets", "qty": 20, "unit": "pcs", "rate": 450.0, "hsn": "7209", "gst_rate": 18, "taxable_value": 9000, "cgst": 810, "sgst": 810, "igst": 0, "item_total": 10620},
        ],
        "subtotal": 9000.0,
        "cgst": 810.0,
        "sgst": 810.0,
        "igst": 0.0,
        "total": 10620.0,
        "tax_type": "CGST+SGST",
        "status": "approved",
        "due_date": datetime.now() + timedelta(days=10),
    },
    {
        "invoice_number": "VYP/2024/0003",
        "order_id": 3,
        "buyer_id": 2,
        "buyer_name": "Suresh Enterprises",
        "buyer_state": "Delhi",
        "line_items": [
            {"name": "Copper Wire", "qty": 50, "unit": "rolls", "rate": 1200.0, "hsn": "7408", "gst_rate": 18, "taxable_value": 60000, "cgst": 0, "sgst": 0, "igst": 10800, "item_total": 70800},
        ],
        "subtotal": 60000.0,
        "cgst": 0.0,
        "sgst": 0.0,
        "igst": 10800.0,
        "total": 70800.0,
        "tax_type": "IGST",
        "status": "overdue",
        "due_date": datetime.now() - timedelta(days=45),
    },
    {
        "invoice_number": "VYP/2024/0004",
        "order_id": 4,
        "buyer_id": 3,
        "buyer_name": "Kaveri Steel Works",
        "buyer_state": "Tamil Nadu",
        "line_items": [
            {"name": "Steel Rods", "qty": 200, "unit": "kg", "rate": 82.0, "hsn": "7214", "gst_rate": 18, "taxable_value": 16400, "cgst": 0, "sgst": 0, "igst": 2952, "item_total": 19352},
            {"name": "Iron Sheets", "qty": 30, "unit": "pcs", "rate": 440.0, "hsn": "7209", "gst_rate": 18, "taxable_value": 13200, "cgst": 0, "sgst": 0, "igst": 2376, "item_total": 15576},
        ],
        "subtotal": 29600.0,
        "cgst": 0.0,
        "sgst": 0.0,
        "igst": 5328.0,
        "total": 34928.0,
        "tax_type": "IGST",
        "status": "draft",
        "due_date": datetime.now() + timedelta(days=25),
    },
]

DUMMY_NOTICES = [
    {
        "raw_text": "ASMT-10 Notice u/s 61 of the CGST Act, 2017. Taxpayer GSTIN 27AAPFU0939F1ZV has been selected for scrutiny of return for tax period 01/2024. Discrepancy detected: Output tax declared in GSTR-3B is less than the tax liability as per auto-populated GSTR-2B by Rs. 12,450. Please furnish explanation within 15 days.",
        "translated_hindi": "GSTIN 27AAPFU0939F1ZV के लिए जनवरी 2024 की GST रिटर्न की जांच की जा रही है। आपकी GSTR-3B में घोषित output tax, GSTR-2B से ₹12,450 कम है। 15 दिनों के अंदर स्पष्टीकरण दें।",
        "action_items": ["CA से परामर्श करें", "GSTR-3B और GSTR-2B का मिलान करें", "15 दिनों में GST पोर्टल पर reply दें"],
        "status": "unreviewed",
    },
    {
        "raw_text": "DRC-01 - Summary of Show Cause Notice u/s 73. Tax demand of Rs. 45,000 along with interest of Rs. 8,100 and penalty of Rs. 4,500 raised for FY 2023-24 Q3. Payment due within 30 days.",
        "translated_hindi": "FY 2023-24 Q3 के लिए ₹45,000 tax + ₹8,100 ब्याज + ₹4,500 जुर्माना = कुल ₹57,600 की मांग की गई है। 30 दिनों में भुगतान करें।",
        "action_items": ["30 दिनों में ₹57,600 का भुगतान करें", "GST पोर्टल पर Challan बनाएं", "CA से legal reply की सलाह लें"],
        "status": "unreviewed",
    },
]

DUMMY_HITL = [
    {
        "action_type": "invoice_draft",
        "payload": {
            "invoice_number": "VYP/2024/0005",
            "order_id": 5,
            "buyer": {"name": "Patel Hardware", "state": "Gujarat", "gstin": "24AAACC1206D1ZM"},
            "seller": {"name": "Sharma Steel Pvt Ltd", "gstin": "27AAPFU0939F1ZV", "state": "Maharashtra"},
            "tax_type": "IGST",
            "line_items": [
                {"name": "Steel Rods", "qty": 500, "unit": "kg", "rate": 88.0, "hsn": "7214", "taxable_value": 44000, "igst": 7920, "item_total": 51920}
            ],
            "subtotal": 44000.0,
            "cgst": 0.0,
            "sgst": 0.0,
            "igst": 7920.0,
            "grand_total": 51920.0,
            "status": "draft",
        },
        "status": "PENDING",
    },
]

DUMMY_TRACES = [
    {"agent_name": "IntakeAgent", "event_type": "completed", "message": "Parsed order from Ramesh bhai: 100kg Steel Rods @ ₹85/kg", "metadata": {"confidence": 0.94}},
    {"agent_name": "GST Agent", "event_type": "completed", "message": "Generated Invoice VYP/2024/0001 — IGST applied (inter-state: MH→KA)", "metadata": {"tax_type": "IGST"}},
    {"agent_name": "CollectionsAgent", "event_type": "thinking", "message": "Evaluating overdue invoices — Suresh Enterprises 45 days overdue (₹70,800)", "metadata": {"risk": "High"}},
    {"agent_name": "Compliance Agent", "event_type": "completed", "message": "ASMT-10 notice translated to Hindi — action items extracted", "metadata": {"severity": "medium"}},
]

DUMMY_NOTICE_TYPES = [
    {"code": "ASMT-10", "description": "Scrutiny of Returns — department found discrepancy in your GST return"},
    {"code": "DRC-01", "description": "Demand Notice — tax, interest and penalty demand raised"},
    {"code": "DRC-03", "description": "Voluntary Payment — you can pay tax/interest/penalty voluntarily"},
    {"code": "REG-03", "description": "Notice for additional information on registration application"},
    {"code": "GSTR-3A", "description": "Default Notice — GSTR-3B not filed within due date"},
]

DUMMY_MSME_SCHEMES = [
    {
        "name": "MUDRA Kishore Loan",
        "min_turnover": 0.0,
        "max_turnover": 5000000.0,
        "benefit": "Loan up to ₹5L at 8.5% PA, no collateral",
        "eligibility": "Annual turnover < ₹50L, operating 2+ years",
        "apply_url": "mudra.org.in",
    },
    {
        "name": "CGTMSE Credit Guarantee",
        "min_turnover": 500000.0,
        "max_turnover": 100000000.0,
        "benefit": "Credit guarantee up to ₹25L — no third-party collateral needed",
        "eligibility": "Manufacturing or service MSMEs registered under MSMED Act",
        "apply_url": "cgtmse.in",
    },
    {
        "name": "PM Vishwakarma Scheme",
        "min_turnover": 0.0,
        "max_turnover": 1500000.0,
        "benefit": "₹3L collateral-free credit, skill training, digital payments incentive",
        "eligibility": "Traditional artisans and craftspeople, turnover < ₹15L",
        "apply_url": "pmvishwakarma.gov.in",
    },
    {
        "name": "TReDS Invoice Financing",
        "min_turnover": 1000000.0,
        "max_turnover": 500000000.0,
        "benefit": "Early payment against trade receivables at competitive rates",
        "eligibility": "MSME supplier to corporates, registered on TReDS platform",
        "apply_url": "treds.in",
    },
    {
        "name": "GeM Seller Registration",
        "min_turnover": 0.0,
        "max_turnover": 100000000.0,
        "benefit": "Sell directly to government departments — guaranteed payment in 10 days",
        "eligibility": "Any registered MSME with Udyam Registration",
        "apply_url": "gem.gov.in",
    },
]


def seed_database():
    db = SessionLocal()
    try:
        # 1. Seed Seller Profile
        if db.query(SellerProfile).count() == 0:
            profile = SellerProfile()
            db.add(profile)
            db.flush()

        # 2. Seed Notice Types
        if db.query(NoticeType).count() == 0:
            for nt in DUMMY_NOTICE_TYPES:
                db.add(NoticeType(**nt))
            db.flush()

        # 3. Seed MSME Schemes
        if db.query(MSMEScheme).count() == 0:
            for ms in DUMMY_MSME_SCHEMES:
                db.add(MSMEScheme(**ms))
            db.flush()

        # 4. Seed Buyers & Invoices & Traces
        if db.query(Buyer).count() == 0:
            for b in DUMMY_BUYERS:
                db.add(Buyer(**b, total_outstanding=random.uniform(10000, 150000)))
            db.flush()

            for inv_data in DUMMY_INVOICES:
                db.add(Invoice(**inv_data))

            for n in DUMMY_NOTICES:
                db.add(GSTNotice(**n))

            for h in DUMMY_HITL:
                db.add(HITLQueue(**h))

            for t in DUMMY_TRACES:
                db.add(AgentTrace(
                    agent=t["agent_name"],
                    event=t["event_type"],
                    status="completed" if t["event_type"] == "completed" else "idle",
                    payload=t.get("metadata"),
                ))

            db.commit()
            print("[Seed] Database successfully seeded with demo data.")
    except Exception as e:
        db.rollback()
        print(f"[Seed] Database seeding failed: {e}")
    finally:
        db.close()
