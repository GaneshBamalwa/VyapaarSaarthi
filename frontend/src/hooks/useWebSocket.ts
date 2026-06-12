import { useEffect, useRef, useCallback } from "react";
import { useAgentStore } from "@/stores/agentStore";
import type { WSEvent } from "@/types";

const WS_URL = `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws`;

let reconnectTimer: ReturnType<typeof setTimeout>;

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const { addEvent } = useAgentStore();

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[WS] Connected");
      useAgentStore.getState().setConnected(true);
      clearTimeout(reconnectTimer);
    };

    ws.onmessage = (evt) => {
      try {
        const event = JSON.parse(evt.data) as WSEvent;
        addEvent(event);
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      console.log("[WS] Disconnected — reconnecting in 3s");
      useAgentStore.getState().setConnected(false);
      reconnectTimer = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [addEvent]);

  useEffect(() => {
    connect();
    const ping = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, 25000);

    return () => {
      clearInterval(ping);
      clearTimeout(reconnectTimer);
      wsRef.current?.close();
    };
  }, [connect]);
}
