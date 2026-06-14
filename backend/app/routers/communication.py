from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.communication.schemas import CommunicationRequest, CommunicationResponse
from app.services.communication_service import CommunicationService

router = APIRouter(prefix="/api/communication", tags=["Communication"])


@router.post("/message", response_model=CommunicationResponse)
async def process_message(
    request: CommunicationRequest, db: Session = Depends(get_db)
) -> CommunicationResponse:
    """Channel-agnostic entry point: parse a natural-language message and run it
    through the shared intent pipeline. Used by Telegram, the voice/calling bot,
    and any future channel."""
    service = CommunicationService(db)
    return await service.process_message(request)
