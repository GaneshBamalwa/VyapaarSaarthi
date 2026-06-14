from fastapi import APIRouter, HTTPException, UploadFile, File
from app.agents.speech import SpeechAgent

router = APIRouter(prefix="/api/speech", tags=["Speech Agent"])
_agent = SpeechAgent()

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg": "MP3",
    "audio/mp3": "MP3",
    "audio/wav": "LINEAR16",
    "audio/flac": "FLAC",
    "audio/ogg": "OGG_OPUS",
    "audio/webm": "WEBM_OPUS",
}


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = "hi-IN",
):
    """Transcribe audio file to text using Vertex AI Speech."""
    encoding = ALLOWED_AUDIO_TYPES.get(file.content_type)
    if not encoding:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type: {file.content_type}. Supported: {list(ALLOWED_AUDIO_TYPES.keys())}",
        )

    audio_bytes = await file.read()
    if len(audio_bytes) > 25 * 1024 * 1024:  # 25MB limit
        raise HTTPException(status_code=400, detail="Audio file too large. Max 25MB.")

    result = await _agent.invoke(
        {
            "audio_bytes": audio_bytes,
            "encoding": encoding,
            "language_code": language,
            "mime_type": file.content_type,
        }
    )

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])

    return result
