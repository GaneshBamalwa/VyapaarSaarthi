from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import date
from app.communication.intents import IntentType

class ExtractedEntity(BaseModel):
    key: str
    value: Any

class CommunicationRequest(BaseModel):
    message_text: str
    user_id: str
    channel: str = "telegram"

class CommunicationResponse(BaseModel):
    intent: IntentType
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str

class IntentParseResult(BaseModel):
    intent: IntentType
    entities: Dict[str, Any] = Field(default_factory=dict)
