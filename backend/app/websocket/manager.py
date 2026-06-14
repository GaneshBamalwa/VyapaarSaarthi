import json
from datetime import datetime
from fastapi import WebSocket
from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConnectionManager:
    def __init__(self):
        self._active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._active.append(websocket)
        logger.info(f"WS connected. Total connections: {len(self._active)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._active:
            self._active.remove(websocket)
        logger.info(f"WS disconnected. Total connections: {len(self._active)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        message["timestamp"] = datetime.utcnow().isoformat()
        payload = json.dumps(message)
        dead: list[WebSocket] = []
        for ws in self._active:
            try:
                await ws.send_text(payload)
            except Exception as e:
                logger.warning(f"WS send failed: {e}")
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def emit_agent_event(
        self,
        agent: str,
        status: str,
        event: str,
        data: Any = None,
        order_id: int | None = None,
        error: str | None = None,
    ) -> None:
        await self.broadcast(
            {
                "type": "agent_event",
                "agent": agent,
                "status": status,
                "event": event,
                "data": data,
                "order_id": order_id,
                "error": error,
            }
        )

    async def emit_hitl_event(self, hitl_id: int, status: str, payload: Any) -> None:
        await self.broadcast(
            {
                "type": "hitl_event",
                "hitl_id": hitl_id,
                "status": status,
                "payload": payload,
            }
        )

    async def emit_order_event(self, order_id: int, status: str, data: Any = None) -> None:
        await self.broadcast(
            {
                "type": "order_event",
                "order_id": order_id,
                "status": status,
                "data": data,
            }
        )

    @property
    def connection_count(self) -> int:
        return len(self._active)


manager = ConnectionManager()
