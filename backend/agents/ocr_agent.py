"""
OCR Agent — extracts text from images and PDFs using Gemini Vision (Pro model).
Handles invoices, WhatsApp screenshots, delivery challans, handwritten notes.
"""
import json
import time
import base64
from utils.gemini_client import generate_multimodal
from utils.ws_manager import ws_manager

SYSTEM_PROMPT = """You are an expert document OCR and classification assistant.
Your job is to extract all text from images, PDFs, and document screenshots.

Rules:
1. Extract ALL visible text accurately, preserving structure where possible.
2. Identify the document type from the content.
3. Rate your confidence in the extraction (0.0 to 1.0).
4. Handle Hindi, English, and mixed text.
5. For WhatsApp screenshots, extract the message content.
6. Always respond with valid JSON only.

Document types: invoice, order, receipt, delivery_challan, whatsapp_message, handwritten_note, unknown

Output format:
{
  "raw_text": "full extracted text",
  "document_type": "one of the types above",
  "language": "hindi|english|mixed",
  "confidence": 0.0 to 1.0,
  "key_fields": {"any key-value pairs detected like amounts, dates, names"}
}"""


async def run(file_bytes: bytes, mime_type: str, filename: str = "document",
              order_id: int = None) -> dict:
    await ws_manager.emit_agent_event("OCRAgent", "running", "extracting_text",
                                      data={"filename": filename}, order_id=order_id)
    start = time.time()
    try:
        image_b64 = base64.b64encode(file_bytes).decode()
        parts = [{"parts": [
            {"inline_data": {"mime_type": mime_type, "data": image_b64}},
            {"text": "Extract all text from this document and return structured JSON."},
        ]}]
        raw = await generate_multimodal(parts, use_pro=True, json_mode=True, system=SYSTEM_PROMPT)
        data = json.loads(raw.strip())
        duration_ms = int((time.time() - start) * 1000)
        await ws_manager.emit_agent_event(
            "OCRAgent", "completed", "text_extracted",
            data={"document_type": data.get("document_type"), "confidence": data.get("confidence")},
            order_id=order_id,
        )
        return {"status": "success", "agent": "OCRAgent", "data": data, "duration_ms": duration_ms}
    except Exception as e:
        await ws_manager.emit_agent_event("OCRAgent", "failed", "extraction_error",
                                          error=str(e), order_id=order_id)
        return {"status": "error", "agent": "OCRAgent", "error": str(e)}
