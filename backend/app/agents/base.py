from abc import ABC, abstractmethod
from typing import Any
from app.websocket.manager import manager
from app.core.logging import get_logger


class BaseAgent(ABC):
    """
    Base class for all Vyapaar Saarthi agents.
    Every agent must implement `invoke()` and can optionally override `_emit`.
    Agents are independently callable and also composable in LangGraph.
    """

    name: str = "BaseAgent"

    def __init__(self):
        self.logger = get_logger(f"agents.{self.name.lower()}")

    @abstractmethod
    async def invoke(self, input_data: Any, **kwargs) -> dict[str, Any]:
        """
        Primary entry point for the agent.
        Returns a standardized result dict.
        """
        ...

    async def _emit(
        self,
        status: str,
        event: str,
        data: Any = None,
        order_id: int | None = None,
        error: str | None = None,
    ) -> None:
        """Emit agent event over WebSocket and persist in DB."""
        await manager.emit_agent_event(
            agent=self.name,
            status=status,
            event=event,
            data=data,
            order_id=order_id,
            error=error,
        )
        try:
            from app.database.session import SessionLocal
            from app.models.agent_trace import AgentTrace
            from datetime import datetime
            with SessionLocal() as db:
                trace = AgentTrace(
                    agent=self.name,
                    event=event,
                    status=status,
                    payload=data,
                    error=error,
                    order_id=order_id,
                    timestamp=datetime.utcnow()
                )
                db.add(trace)
                db.commit()
        except Exception as e:
            self.logger.warning(f"Failed to persist agent trace: {e}")


    def _success(self, data: Any, **meta) -> dict[str, Any]:
        return {"status": "success", "agent": self.name, "data": data, **meta}

    def _failure(self, error: str, **meta) -> dict[str, Any]:
        return {"status": "error", "agent": self.name, "error": error, **meta}
