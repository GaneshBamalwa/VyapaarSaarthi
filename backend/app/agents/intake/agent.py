import json
import time
from typing import Any

from app.agents.base import BaseAgent
from app.agents.intake.prompt import INTAKE_SYSTEM_PROMPT, INTAKE_USER_TEMPLATE
from app.agents.intake.schemas import IntakeInput, IntakeOutput
from app.core.gemini_client import get_gemini_client
from app.core.config import get_settings

settings = get_settings()


class IntakeAgent(BaseAgent):
    name = "IntakeAgent"

    async def invoke(self, input_data: IntakeInput | dict, **kwargs) -> dict[str, Any]:
        if isinstance(input_data, dict):
            input_data = IntakeInput(**input_data)

        order_id = kwargs.get("order_id")
        await self._emit("running", "parsing_order", order_id=order_id)
        start = time.time()

        try:
            client = get_gemini_client()
            prompt = INTAKE_USER_TEMPLATE.format(input_text=input_data.text)

            import datetime
            current_time = datetime.datetime.now().strftime("%A, %Y-%m-%d %I:%M %p")
            dynamic_system_prompt = f"{INTAKE_SYSTEM_PROMPT}\n\nCRITICAL CONTEXT: The current real-world date and time is {current_time}. Use this to accurately calculate relative dates like 'tomorrow', 'next week', 'aaj', 'kal', etc."

            response = client.models.generate_content(
                model=settings.GEMINI_FLASH_MODEL,
                contents=prompt,
                config={
                    "system_instruction": dynamic_system_prompt,
                    "response_mime_type": "application/json",
                    "temperature": 0.1,
                },
            )

            raw_json = response.text.strip()
            data = json.loads(raw_json)
            output = IntakeOutput(**data)

            duration_ms = int((time.time() - start) * 1000)
            await self._emit(
                "completed",
                "order_parsed",
                data=output.model_dump(),
                order_id=order_id,
            )

            return self._success(output.model_dump(), duration_ms=duration_ms)

        except json.JSONDecodeError as e:
            await self._emit("failed", "parse_error", error=str(e), order_id=order_id)
            return self._failure(f"JSON parsing failed: {e}")
        except Exception as e:
            self.logger.error(f"IntakeAgent error: {e}")
            await self._emit("failed", "agent_error", error=str(e), order_id=order_id)
            return self._failure(str(e))
