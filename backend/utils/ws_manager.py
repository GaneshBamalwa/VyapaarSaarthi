"""WebSocket connection manager — unified for both GST agents and order intake agents."""
from fastapi import WebSocket
from typing import List, Any
import json
from datetime import datetime


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        message.setdefault("timestamp", datetime.utcnow().isoformat())
        payload = json.dumps(message)
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for d in dead:
            self.disconnect(d)

    # ── Legacy broadcast used by GST / compliance agents ──────────────────
    async def broadcast_agent(self, agent_name: str, event_type: str,
                               message: str, metadata: dict = None):
        await self.broadcast({
            "type": "agent_event",
            "agent": agent_name,
            "event": event_type,
            "message": message,
            "metadata": metadata or {},
        })

    # ── VyapaarSaarthi-style emit methods (used by intake/OCR/speech agents) ─
    async def emit_agent_event(self, agent: str, status: str, event: str,
                                data: Any = None, order_id: int = None,
                                error: str = None):
        await self.broadcast({
            "type": "agent_event",
            "agent": agent,
            "status": status,
            "event": event,
            "message": event.replace("_", " ").title(),
            "data": data,
            "order_id": order_id,
            "error": error,
        })

    async def emit_hitl_event(self, hitl_id: int, status: str, payload: Any):
        await self.broadcast({
            "type": "hitl_event",
            "hitl_id": hitl_id,
            "status": status,
            "payload": payload,
        })

    async def emit_order_event(self, order_id: int, status: str, data: Any = None):
        await self.broadcast({
            "type": "order_event",
            "order_id": order_id,
            "status": status,
            "data": data,
        })

    @property
    def connection_count(self):
        return len(self.active_connections)


ws_manager = ConnectionManager()
