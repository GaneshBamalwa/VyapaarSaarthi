import json
import time
from typing import Any

from app.agents.base import BaseAgent
from app.agents.clarification.prompt import (
    CLARIFICATION_SYSTEM_PROMPT,
    CLARIFICATION_USER_TEMPLATE,
)
from app.core.gemini_client import get_gemini_client
from app.core.config import get_settings

settings = get_settings()


class ClarificationAgent(BaseAgent):
    name = "ClarificationAgent"

    async def invoke(self, input_data: dict | str, **kwargs) -> dict[str, Any]:
        if isinstance(input_data, str):
            text = input_data
        else:
            text = input_data.get("text", "")

        order_id = kwargs.get("order_id")
        await self._emit("running", "checking_ambiguity", order_id=order_id)
        start = time.time()

        try:
            client = get_gemini_client()
            prompt = CLARIFICATION_USER_TEMPLATE.format(input_text=text)

            response = client.models.generate_content(
                model=settings.GEMINI_FLASH_MODEL,
                contents=prompt,
                config={
                    "system_instruction": CLARIFICATION_SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                },
            )

            data = json.loads(response.text.strip())
            duration_ms = int((time.time() - start) * 1000)

            status_event = "order_ambiguous" if data.get("status") == "AMBIGUOUS" else "order_clear"
            await self._emit("completed", status_event, data=data, order_id=order_id)

            return self._success(data, duration_ms=duration_ms)

        except Exception as e:
            self.logger.error(f"ClarificationAgent error: {e}")
            await self._emit("failed", "agent_error", error=str(e), order_id=order_id)
            return self._failure(str(e))
