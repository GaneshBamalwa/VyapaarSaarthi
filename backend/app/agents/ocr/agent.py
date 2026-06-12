import json
import time
import base64
from typing import Any

from app.agents.base import BaseAgent
from app.agents.ocr.prompt import OCR_SYSTEM_PROMPT
from app.core.gemini_client import get_gemini_client
from app.core.config import get_settings

settings = get_settings()


class OCRAgent(BaseAgent):
    name = "OCRAgent"

    async def invoke(self, input_data: dict, **kwargs) -> dict[str, Any]:
        """
        input_data: {
            "file_bytes": bytes,
            "mime_type": str,  # image/jpeg, image/png, application/pdf
            "filename": str
        }
        """
        file_bytes = input_data.get("file_bytes", b"")
        mime_type = input_data.get("mime_type", "image/jpeg")
        filename = input_data.get("filename", "document")
        order_id = kwargs.get("order_id")

        await self._emit("running", "extracting_text", data={"filename": filename}, order_id=order_id)
        start = time.time()

        try:
            client = get_gemini_client()

            # Encode image for Gemini Vision
            image_b64 = base64.b64encode(file_bytes).decode()

            response = client.models.generate_content(
                model=settings.GEMINI_PRO_MODEL,
                contents=[
                    {
                        "parts": [
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": image_b64,
                                }
                            },
                            {
                                "text": "Extract all text from this document and return structured JSON."
                            },
                        ]
                    }
                ],
                config={
                    "system_instruction": OCR_SYSTEM_PROMPT,
                    "response_mime_type": "application/json",
                    "temperature": 0.05,
                },
            )

            data = json.loads(response.text.strip())
            duration_ms = int((time.time() - start) * 1000)

            await self._emit(
                "completed",
                "text_extracted",
                data={"document_type": data.get("document_type"), "confidence": data.get("confidence")},
                order_id=order_id,
            )

            return self._success(data, duration_ms=duration_ms)

        except Exception as e:
            self.logger.error(f"OCRAgent error: {e}")
            await self._emit("failed", "extraction_error", error=str(e), order_id=order_id)
            return self._failure(str(e))
