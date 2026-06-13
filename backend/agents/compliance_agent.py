"""
GST Compliance & Advisory Agent
- Translates complex GST notices to simple Hindi
- Extracts action items from penalty notices
- Matches MSME schemes
- GSTR summary computed from real invoice data
"""
import json
from datetime import datetime
from typing import Optional
from utils import gemini_client as _gc
from utils.ws_manager import ws_manager


async def translate_gst_notice(raw_notice_text: str, notice_types: dict) -> dict:
    await ws_manager.broadcast_agent("Compliance Agent", "thinking", "Analyzing GST notice content...")

    notice_type = "Unknown"
    for code, desc in notice_types.items():
        if code in raw_notice_text.upper():
            notice_type = f"{code} — {desc}"
            break

    prompt = f"""You are an expert GST consultant helping an MSME owner understand a tax notice.
Notice type: {notice_type}
Notice text: {raw_notice_text[:2000]}

Translate this into simple, actionable Hindi. Respond in JSON:
{{
  "hindi_translation": "...",
  "notice_type": "...",
  "severity": "low|medium|high",
  "deadline": "YYYY-MM-DD or null",
  "penalty_amount": 0,
  "action_items": ["step 1", "step 2", "step 3"],
  "escalation_required": false
}}"""

    await ws_manager.broadcast_agent("Compliance Agent", "tool_call", "Calling Gemini for notice translation...")
    response = await _gc.generate_text(prompt, use_pro=True, json_mode=True)

    try:
        result = json.loads(response)
    except Exception as e:
        await ws_manager.broadcast_agent(
            "Compliance Agent", "failed",
            f"Failed to parse AI response: {str(e)}"
        )
        raise Exception(f"Failed to parse GST notice translation from AI: {str(e)}")

    await ws_manager.broadcast_agent(
        "Compliance Agent", "completed",
        f"Notice translated — severity: {result.get('severity', 'unknown')}",
    )
    return result


async def match_msme_schemes(annual_turnover: float, employee_count: int, category: str, schemes: list) -> list:
    await ws_manager.broadcast_agent("Compliance Agent", "thinking", "Scanning MSME scheme eligibility...")

    matching = []
    for scheme in schemes:
        if scheme["min_turnover"] <= annual_turnover <= scheme["max_turnover"]:
            score = max(10, min(99, round(100 - (annual_turnover / max(scheme["max_turnover"], 1)) * 60)))
            matching.append({
                **scheme,
                "match_reason": f"Annual turnover ₹{annual_turnover/100000:.1f}L falls within scheme range",
                "match_score": score,
            })

    await ws_manager.broadcast_agent(
        "Compliance Agent", "completed",
        f"Found {len(matching)} matching schemes for your business profile",
    )
    return matching


async def generate_gstr_summary(invoices: list, period: str) -> dict:
    await ws_manager.broadcast_agent("Compliance Agent", "thinking", f"Generating GSTR summary for {period}...")

    b2b = [i for i in invoices if i.get("buyer_gstin") and i["buyer_gstin"] not in ("N/A", "", None)]
    b2c = [i for i in invoices if not i.get("buyer_gstin") or i["buyer_gstin"] in ("N/A", "", None)]

    total_taxable = sum(i.get("subtotal", 0) for i in invoices)
    total_cgst = sum(i.get("cgst", 0) for i in invoices)
    total_sgst = sum(i.get("sgst", 0) for i in invoices)
    total_igst = sum(i.get("igst", 0) for i in invoices)
    total_tax = total_cgst + total_sgst + total_igst

    summary = {
        "period": period,
        "b2b_invoice_count": len(b2b),
        "b2c_invoice_count": len(b2c),
        "total_taxable_value": round(total_taxable, 2),
        "total_cgst": round(total_cgst, 2),
        "total_sgst": round(total_sgst, 2),
        "total_igst": round(total_igst, 2),
        "total_tax_liability": round(total_tax, 2),
        "estimated_itc": round(total_tax * 0.4, 2),
        "net_payable": round(total_tax * 0.6, 2),
        "filing_status": "Ready to File" if invoices else "No invoices this period",
    }

    await ws_manager.broadcast_agent("Compliance Agent", "completed",
        f"GSTR summary ready — net payable ₹{summary['net_payable']:,.2f}")
    return summary
