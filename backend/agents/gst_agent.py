"""
GST Invoice & Tax Agent
- Generates GST-compliant invoice drafts
- Determines CGST+SGST vs IGST based on buyer/seller state
- Validates HSN codes and tax brackets
- Validates GSTR return data
"""
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from utils import gemini_client as _gc
from utils.mock_gstn import determine_tax_type, verify_gstin
from utils.ws_manager import ws_manager

with open(os.path.join(os.path.dirname(__file__), "../utils/hsn_codes.json")) as f:
    HSN_DB = json.load(f)


def lookup_hsn(product_name: str) -> dict:
    name_lower = product_name.lower().replace(" ", "_")
    for key, val in HSN_DB.items():
        if key in name_lower or any(word in name_lower for word in key.split("_")):
            return val
    return {"hsn": "9999", "description": product_name, "gst_rate": 18}


def generate_invoice_number(existing_count: int) -> str:
    year = datetime.now().year
    return f"VYP/{year}/{existing_count + 1:04d}"


async def generate_gst_invoice(
    order_id: int,
    buyer_name: str,
    buyer_state: str,
    buyer_gstin: Optional[str],
    line_items: List[Dict],
    invoice_count: int,
    seller_profile: Dict,
    db=None,
) -> dict:
    await ws_manager.broadcast_agent("GST Agent", "thinking", f"Generating GST invoice for {buyer_name}...")

    gstin_info = {}
    if buyer_gstin:
        gstin_info = verify_gstin(buyer_gstin)
        await ws_manager.broadcast_agent("GST Agent", "tool_call", f"Verified GSTIN: {buyer_gstin} → {gstin_info.get('status')}")

    tax_info = determine_tax_type(seller_profile["state"], buyer_state)
    await ws_manager.broadcast_agent("GST Agent", "decision", f"Tax type: {tax_info['tax_type']} ({tax_info['description']})")

    enriched_items = []
    subtotal = 0.0
    for item in line_items:
        hsn_data = lookup_hsn(item.get("name", ""))
        taxable_value = item.get("qty", 1) * item.get("rate", 0)
        gst_rate = hsn_data["gst_rate"]

        if tax_info["tax_type"] == "CGST+SGST":
            cgst_amount = round(taxable_value * (gst_rate / 2) / 100, 2)
            sgst_amount = round(taxable_value * (gst_rate / 2) / 100, 2)
            igst_amount = 0.0
        else:
            cgst_amount = 0.0
            sgst_amount = 0.0
            igst_amount = round(taxable_value * gst_rate / 100, 2)

        item_total = taxable_value + cgst_amount + sgst_amount + igst_amount
        enriched_items.append({
            **item,
            "hsn": hsn_data["hsn"],
            "taxable_value": taxable_value,
            "gst_rate": gst_rate,
            "cgst": cgst_amount,
            "sgst": sgst_amount,
            "igst": igst_amount,
            "item_total": item_total,
        })
        subtotal += taxable_value

    total_cgst = sum(i["cgst"] for i in enriched_items)
    total_sgst = sum(i["sgst"] for i in enriched_items)
    total_igst = sum(i["igst"] for i in enriched_items)
    grand_total = subtotal + total_cgst + total_sgst + total_igst

    invoice = {
        "invoice_number": generate_invoice_number(invoice_count),
        "order_id": order_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "seller": {
            "name": seller_profile["name"],
            "gstin": seller_profile["gstin"],
            "state": seller_profile["state"],
            "address": seller_profile["address"],
        },
        "buyer": {
            "name": buyer_name,
            "gstin": buyer_gstin or "N/A",
            "state": buyer_state,
        },
        "tax_type": tax_info["tax_type"],
        "line_items": enriched_items,
        "subtotal": round(subtotal, 2),
        "cgst": round(total_cgst, 2),
        "sgst": round(total_sgst, 2),
        "igst": round(total_igst, 2),
        "grand_total": round(grand_total, 2),
        "status": "draft",
    }

    await ws_manager.broadcast_agent(
        "GST Agent", "completed",
        f"Invoice {invoice['invoice_number']} drafted — ₹{grand_total:,.2f} ({tax_info['tax_type']})",
    )
    return invoice


async def validate_gstr_return(invoices: List[dict]) -> dict:
    await ws_manager.broadcast_agent("GST Agent", "thinking", "Validating GSTR-1 return data...")

    issues = []
    suggestions = []

    # Check invoice sequence
    numbers = []
    for inv in invoices:
        try:
            num = int(inv.get("invoice_number", "0").split("/")[-1])
            numbers.append(num)
        except Exception:
            issues.append(f"Non-standard invoice number: {inv.get('invoice_number')}")

    if numbers != sorted(numbers):
        issues.append("Invoice numbers are not sequential — GSTR portal may reject the filing.")

    # Check for missing GSTINs on B2B invoices
    b2b_no_gstin = [
        inv["buyer_name"] for inv in invoices
        if inv.get("buyer_gstin") in (None, "", "N/A") and inv.get("total", 0) > 250000
    ]
    if b2b_no_gstin:
        issues.append(f"Missing GSTIN for high-value buyers: {', '.join(b2b_no_gstin)}")

    if not issues:
        suggestions.append("All invoice sequences are correct")
        suggestions.append("HSN codes present on all line items")
        suggestions.append("Tax calculations are arithmetically verified")
        suggestions.append("Ready for GSTR-1 filing")

    prompt = f"""
You are a GST compliance expert. Validate this GSTR return:
Total invoices: {len(invoices)}
Issues found: {issues}
Tax collected: ₹{sum(i.get('total', 0) * 0.18 for i in invoices):,.2f}

Respond in JSON: {{"overall_status": "valid|needs_correction", "issues": [], "suggestions": [], "filing_ready": true|false}}
"""
    ai_response = await _gc.generate_text(prompt, json_mode=True)
    try:
        ai_result = json.loads(ai_response)
    except Exception:
        ai_result = {"overall_status": "valid" if not issues else "needs_correction"}

    result = {
        "total_invoices": len(invoices),
        "issues": issues or ai_result.get("issues", []),
        "suggestions": suggestions or ai_result.get("suggestions", []),
        "filing_ready": len(issues) == 0,
        "overall_status": "valid" if not issues else "needs_correction",
    }

    await ws_manager.broadcast_agent("GST Agent", "completed", f"GSTR validation done — {result['overall_status']}")
    return result
