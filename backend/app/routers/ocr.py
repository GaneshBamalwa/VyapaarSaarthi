from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.agents.ocr import OCRAgent

router = APIRouter(prefix="/api/ocr", tags=["OCR Agent"])
_agent = OCRAgent()


@router.post("/extract")
async def extract_text(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Extract text from uploaded image or PDF using Gemini Vision."""
    allowed_types = {
        "image/jpeg", "image/png", "image/webp",
        "image/gif", "application/pdf"
    }
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    result = await _agent.invoke(
        {
            "file_bytes": file_bytes,
            "mime_type": file.content_type,
            "filename": file.filename,
        }
    )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])

    return result
