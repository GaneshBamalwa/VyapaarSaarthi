from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class AgentEventPayload(BaseModel):
    agent: str
    status: str  # running | completed | failed | waiting
    event: str
    data: Optional[Any] = None
    error: Optional[str] = None
    order_id: Optional[int] = None
    timestamp: datetime = datetime.utcnow()


class AgentTraceResponse(BaseModel):
    id: int
    agent: str
    event: str
    status: str
    payload: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    order_id: Optional[int] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class AgentTraceListResponse(BaseModel):
    total: int
    traces: list[AgentTraceResponse]
