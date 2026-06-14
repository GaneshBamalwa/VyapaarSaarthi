from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.agent_trace_repository import AgentTraceRepository
from app.schemas.agent import AgentTraceListResponse, AgentTraceResponse

router = APIRouter(prefix="/api/agents", tags=["Agent Traces"])


@router.get("/traces", response_model=AgentTraceListResponse)
async def get_traces(limit: int = 100, db: Session = Depends(get_db)):
    repo = AgentTraceRepository(db)
    traces = repo.list_recent(limit=limit)
    return AgentTraceListResponse(
        total=len(traces),
        traces=[AgentTraceResponse.model_validate(t) for t in traces]
    )


@router.get("/traces/{agent_name}", response_model=AgentTraceListResponse)
async def get_traces_by_agent(agent_name: str, limit: int = 50, db: Session = Depends(get_db)):
    repo = AgentTraceRepository(db)
    traces = repo.list_by_agent(agent_name, limit=limit)
    return AgentTraceListResponse(
        total=len(traces),
        traces=[AgentTraceResponse.model_validate(t) for t in traces]
    )
