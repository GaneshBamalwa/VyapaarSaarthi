from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from typing import Optional
from app.models.agent_trace import AgentTrace
from app.schemas.agent import AgentEventPayload


class AgentTraceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, payload: AgentEventPayload, duration_ms: Optional[int] = None) -> AgentTrace:
        trace = AgentTrace(
            agent=payload.agent,
            event=payload.event,
            status=payload.status,
            payload=payload.data,
            error=payload.error,
            duration_ms=duration_ms,
            order_id=payload.order_id,
            timestamp=datetime.utcnow(),
        )
        self.db.add(trace)
        self.db.commit()
        self.db.refresh(trace)
        return trace

    def list_recent(self, limit: int = 100) -> list[AgentTrace]:
        return (
            self.db.query(AgentTrace)
            .order_by(desc(AgentTrace.timestamp))
            .limit(limit)
            .all()
        )

    def list_by_agent(self, agent: str, limit: int = 50) -> list[AgentTrace]:
        return (
            self.db.query(AgentTrace)
            .filter(AgentTrace.agent == agent)
            .order_by(desc(AgentTrace.timestamp))
            .limit(limit)
            .all()
        )

    def count_total(self) -> int:
        return self.db.query(AgentTrace).count()
