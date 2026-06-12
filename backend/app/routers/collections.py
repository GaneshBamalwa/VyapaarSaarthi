from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.agents.collections import CollectionsAgent

router = APIRouter(prefix="/api/collections", tags=["Collections Agent"])
_agent = CollectionsAgent()


class CollectionsRequest(BaseModel):
    invoice_id: str
    customer: str = "Customer"
    amount: float = 0.0
    due_days: int = 0
    previous_reminders: int = 0


@router.post("/analyze")
async def analyze_collection(body: CollectionsRequest):
    """Analyze overdue invoice and generate Hindi reminder."""
    result = await _agent.invoke(body.model_dump())
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])
    return result
