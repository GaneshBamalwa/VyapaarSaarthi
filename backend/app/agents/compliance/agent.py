import json
from datetime import datetime
from typing import Any
from app.agents.base import BaseAgent
from app.core import gemini_client as _gc


class ComplianceAgent(BaseAgent):
    name = "Compliance Agent"

    async def invoke(self, input_data: dict, **kwargs) -> dict[str, Any]:
        action = input_data.get("action", "translate_notice")
        try:
            if action == "translate_notice":
                res = await self.translate_gst_notice(
                    raw_notice_text=input_data.get("raw_notice_text", ""),
                    notice_types=input_data.get("notice_types", {}),
                )
                return self._success(res)
            elif action == "match_schemes":
                res = await self.match_msme_schemes(
                    annual_turnover=input_data.get("annual_turnover", 0.0),
                    employee_count=input_data.get("employee_count", 0),
                    category=input_data.get("category", "General"),
                    schemes=input_data.get("schemes", []),
                )
                return self._success(res)
            elif action == "gstr_summary":
                res = await self.generate_gstr_summary(
                    invoices=input_data.get("invoices", []),
                    period=input_data.get("period", ""),
                )
                return self._success(res)
            return self._failure(f"Unknown action: {action}")
        except Exception as e:
            self.logger.error(f"ComplianceAgent execution failed: {e}")
            return self._failure(str(e))

    async def translate_gst_notice(self, raw_notice_text: str, notice_types: dict) -> dict:
        await self._emit("running", "analyzing_notice")

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

        await self._emit("running", "calling_ai_translation")
        response = await _gc.generate_text(prompt, use_pro=True, json_mode=True)

        try:
            result = json.loads(response)
        except Exception as e:
            await self._emit("failed", "ai_parsing_failed", error=str(e))
            raise Exception(f"Failed to parse GST notice translation from AI: {str(e)}")

        await self._emit("completed", "notice_translated", data={"severity": result.get("severity")})
        return result

    async def match_msme_schemes(self, annual_turnover: float, employee_count: int, category: str, schemes: list) -> list:
        await self._emit("running", "scanning_schemes")

        matching = []
        for scheme in schemes:
            if scheme.get("min_turnover", 0.0) <= annual_turnover <= scheme.get("max_turnover", 0.0):
                score = max(10, min(99, round(100 - (annual_turnover / max(scheme.get("max_turnover", 1.0), 1.0)) * 60)))
                matching.append({
                    **scheme,
                    "match_reason": f"Annual turnover ₹{annual_turnover/100000:.1f}L falls within scheme range",
                    "match_score": score,
                })

        await self._emit("completed", "schemes_matched", data={"match_count": len(matching)})
        return matching

    async def generate_gstr_summary(self, invoices: list, period: str) -> dict:
        await self._emit("running", "summarizing_gstr", data={"period": period})

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

        await self._emit("completed", "gstr_summary_generated", data={"net_payable": summary["net_payable"]})
        return summary
