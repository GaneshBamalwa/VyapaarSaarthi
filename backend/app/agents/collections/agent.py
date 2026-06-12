import json
import time
from typing import Any

from app.agents.base import BaseAgent
from app.agents.collections.prompt import COLLECTIONS_SYSTEM_PROMPT, COLLECTIONS_USER_TEMPLATE
from app.core.gemini_client import get_gemini_client
from app.core.config import get_settings

settings = get_settings()


class CollectionsAgent(BaseAgent):
    name = "CollectionsAgent"

    async def invoke(self, input_data: dict, **kwargs) -> dict[str, Any]:
        """
        input_data: {
            "invoice_id": str,
            "customer": str,
            "amount": float,
            "due_days": int,
            "previous_reminders": int (default 0)
        }
        """
        invoice_id = input_data.get("invoice_id", "")
        customer = input_data.get("customer", "Customer")
        amount = input_data.get("amount", 0)
        due_days = input_data.get("due_days", 0)
        previous_reminders = input_data.get("previous_reminders", 0)

        await self._emit("running", "analyzing_invoice", data={"invoice_id": invoice_id})
        start = time.time()

        try:
            client = get_gemini_client()
            prompt = COLLECTIONS_USER_TEMPLATE.format(
                invoice_id=invoice_id,
                customer=customer,
                amount=amount,
                due_days=due_days,
                previous_reminders=previous_reminders,
            )

            response = client.models.generate_content(
                model=settings.GEMINI_FLASH_MODEL,
                contents=prompt,
                config={
                    "system_instruction": COLLECTIONS_SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                    "temperature": 0.2,
                },
            )

            data = json.loads(response.text.strip())
            duration_ms = int((time.time() - start) * 1000)

            await self._emit(
                "completed",
                "reminder_generated",
                data={"risk": data.get("risk"), "invoice_id": invoice_id},
            )

            return self._success(data, duration_ms=duration_ms)

        except Exception as e:
            self.logger.error(f"CollectionsAgent error: {e}")
            await self._emit("failed", "agent_error", error=str(e))
            return self._failure(str(e))
