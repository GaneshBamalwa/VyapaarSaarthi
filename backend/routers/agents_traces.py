from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, AgentTrace

router = APIRouter(prefix="/api/agents", tags=["agents"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/traces")
def get_traces(limit: int = 50, db: Session = Depends(get_db)):
    traces = (
        db.query(AgentTrace)
        .order_by(AgentTrace.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": t.id,
            "agent_name": t.agent_name,
            "status": t.event_type,
            "event": t.message,
            "data": t.trace_metadata,
            "timestamp": str(t.created_at),
        }
        for t in traces
    ]
