from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from app.database.session import Base


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id = Column(Integer, primary_key=True, index=True)
    agent = Column(String(100), nullable=False, index=True)
    event = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # running, completed, failed
    payload = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    order_id = Column(Integer, nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<AgentTrace id={self.id} agent={self.agent} event={self.event}>"
