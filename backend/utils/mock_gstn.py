"""Mock GSTN portal responses — no live credentials needed."""
import random
from datetime import datetime, timedelta


MOCK_GSTIN_DB = {
    "27AAPFU0939F1ZV": {"name": "Sharma Steel Pvt Ltd", "state": "Maharashtra", "status": "Active"},
    "29AABCT1332L1ZK": {"name": "Kaveri Traders", "state": "Karnataka", "status": "Active"},
    "07AAACR5055K1Z5": {"name": "Delhi Iron Works", "state": "Delhi", "status": "Active"},
    "33AABCS1429B1Z0": {"name": "Chennai Exports", "state": "Tamil Nadu", "status": "Active"},
    "24AAACC1206D1ZM": {"name": "Ahmedabad Goods", "state": "Gujarat", "status": "Active"},
    "INVALID123": {"name": "", "state": "", "status": "Invalid"},
}

STATE_CODES = {
    "Maharashtra": "27", "Karnataka": "29", "Delhi": "07",
    "Tamil Nadu": "33", "Gujarat": "24", "Uttar Pradesh": "09",
    "West Bengal": "19", "Rajasthan": "08", "Telangana": "36",
}


def verify_gstin(gstin: str) -> dict:
    if gstin in MOCK_GSTIN_DB:
        return {"valid": MOCK_GSTIN_DB[gstin]["status"] == "Active", **MOCK_GSTIN_DB[gstin]}
    return {"valid": False, "name": "", "state": "Unknown", "status": "Not Found"}


def get_gstr1_summary(gstin: str, month: int, year: int) -> dict:
    return {
        "gstin": gstin,
        "period": f"{month:02d}/{year}",
        "b2b_invoices": random.randint(5, 20),
        "b2c_invoices": random.randint(10, 40),
        "total_taxable_value": round(random.uniform(200000, 800000), 2),
        "total_tax_collected": round(random.uniform(20000, 80000), 2),
        "filing_status": random.choice(["Filed", "Pending", "Pending"]),
        "due_date": f"{year}-{month:02d}-11",
    }


def get_input_tax_credit(gstin: str) -> dict:
    return {
        "gstin": gstin,
        "available_itc": round(random.uniform(10000, 50000), 2),
        "utilized_itc": round(random.uniform(5000, 20000), 2),
        "blocked_credit": round(random.uniform(0, 5000), 2),
        "last_updated": datetime.utcnow().isoformat(),
    }


def determine_tax_type(seller_state: str, buyer_state: str) -> dict:
    if seller_state == buyer_state:
        return {"tax_type": "CGST+SGST", "rate_each": 9.0, "description": "Intra-state supply"}
    return {"tax_type": "IGST", "rate": 18.0, "description": "Inter-state supply"}
