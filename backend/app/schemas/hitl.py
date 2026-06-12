from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from app.models.hitl_queue import HITLStatus


class HITLQueueResponse(BaseModel):
    id: int
    order_id: Optional[int] = None
    graph_thread_id: Optional[str] = None
    status: HITLStatus
    reason: Optional[str] = None
    payload: Any
    edited_payload: Optional[Any] = None
    reviewer_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HITLResolveRequest(BaseModel):
    action: str  # approve | reject | edit
    edited_payload: Optional[Any] = None
    reviewer_notes: Optional[str] = None


class HITLListResponse(BaseModel):
    total: int
    items: list[HITLQueueResponse]
