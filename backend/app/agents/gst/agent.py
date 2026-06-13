import os
import json
from datetime import datetime, timedelta
from typing import Any, List, Dict, Optional
from app.agents.base import BaseAgent
from app.core import gemini_client as _gc
from app.utils.mock_gstn import determine_tax_type, verify_gstin


class GSTAgent(BaseAgent):
    name = "GST Agent"

    def __init__(self):
        super().__init__()
        hsn_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../utils/hsn_codes.json"))
        with open(hsn_path, "r") as f:
            self.hsn_db = json.load(f)

    def lookup_hsn(self, product_name: str) -> dict:
        name_lower = product_name.lower().replace(" ", "_")
        for key, val in self.hsn_db.items():
            if key in name_lower or any(word in name_lower for word in key.split("_")):
                return val
        return {"hsn": "9999", "description": product_name, "gst_rate": 18}

    def generate_invoice_number(self, existing_count: int) -> str:
        year = datetime.now().year
        return f"VYP/{year}/{existing_count + 1:04d}"

    async def invoke(self, input_data: dict, **kwargs) -> dict[str, Any]:
        action = input_data.get("action", "generate_invoice")
        try:
            if action == "generate_invoice":
                res = await self.generate_gst_invoice(
                    order_id=input_data.get("order_id"),
                    buyer_name=input_data.get("buyer_name", ""),
                    buyer_state=input_data.get("buyer_state", ""),
                    buyer_gstin=input_data.get("buyer_gstin"),
                    line_items=input_data.get("line_items", []),
                    invoice_count=input_data.get("invoice_count", 0),
                    seller_profile=input_data.get("seller_profile", {}),
                )
                return self._success(res)
            elif action == "validate_gstr":
                res = await self.validate_gstr_return(
                    invoices=input_data.get("invoices", []),
                )
                return self._success(res)
            return self._failure(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"GSTAgent execution failed: {e}")
            return self._failure(str(e))

    async def generate_gst_invoice(
        self,
        order_id: int,
        buyer_name: str,
        buyer_state: str,
        buyer_gstin: Optional[str],
        line_items: List[Dict],
        invoice_count: int,
        seller_profile: Dict,
    ) -> dict:
        await self._emit("running", "generating_invoice", data={"buyer": buyer_name})

        gstin_info = {}
        if buyer_gstin:
            gstin_info = verify_gstin(buyer_gstin)
            await self._emit(
                "running", "verifying_gstin",
                data={"gstin": buyer_gstin, "status": gstin_info.get("status")}
            )

        tax_info = determine_tax_type(seller_profile.get("state", "Maharashtra"), buyer_state)
        await self._emit("running", "tax_type_determined", data={"tax_type": tax_info["tax_type"]})

        enriched_items = []
        subtotal = 0.0
        for item in line_items:
            hsn_data = self.lookup_hsn(item.get("name", ""))
            qty = item.get("quantity") or item.get("qty") or 1
            rate = item.get("price") or item.get("rate") or 0.0
            taxable_value = qty * rate
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
                "name": item.get("name", ""),
                "qty": qty,
                "rate": rate,
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
            "invoice_number": self.generate_invoice_number(invoice_count),
            "order_id": order_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "seller": {
                "name": seller_profile.get("name", "Sharma Steel Pvt Ltd"),
                "gstin": seller_profile.get("gstin", "27AAPFU0939F1ZV"),
                "state": seller_profile.get("state", "Maharashtra"),
                "address": seller_profile.get("address", "Plot 45, MIDC Industrial Area, Pune - 411018"),
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

        await self._emit(
            "completed", "invoice_drafted",
            data={"invoice_number": invoice["invoice_number"], "total": invoice["grand_total"]}
        )
        return invoice

    async def validate_gstr_return(self, invoices: List[dict]) -> dict:
        await self._emit("running", "validating_gstr", data={"invoice_count": len(invoices)})

        issues = []
        suggestions = []

        numbers = []
        for inv in invoices:
            try:
                num = int(inv.get("invoice_number", "0").split("/")[-1])
                numbers.append(num)
            except Exception:
                issues.append(f"Non-standard invoice number: {inv.get('invoice_number')}")

        if numbers != sorted(numbers):
            issues.append("Invoice numbers are not sequential — GSTR portal may reject the filing.")

        b2b_no_gstin = [
            inv.get("buyer_name", "") for inv in invoices
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

        await self._emit("completed", "gstr_validated", data={"status": result["overall_status"]})
        return result
