from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from agents.ocr_agent import run as ocr_run

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/extract")
async def extract_document(
    file: UploadFile = File(...),
    order_id: Optional[int] = Form(None),
):
    file_bytes = await file.read()
    mime_type = file.content_type or "application/octet-stream"
    return await ocr_run(file_bytes, mime_type, file.filename or "document", order_id)
