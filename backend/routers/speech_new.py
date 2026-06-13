from fastapi import APIRouter, UploadFile, File, Form
from typing import Optional
from agents.speech_agent import run as speech_run

router = APIRouter(prefix="/api/speech", tags=["speech"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form("hi-IN"),
    order_id: Optional[int] = Form(None),
):
    audio_bytes = await file.read()
    mime_type = file.content_type or "audio/mp3"
    return await speech_run(audio_bytes, language, mime_type, order_id)
