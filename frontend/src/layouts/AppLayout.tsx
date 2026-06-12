import { Outlet } from "react-router-dom";
import { Sidebar } from "@/components/Sidebar";
import { SimulatorPanel } from "@/components/SimulatorPanel";
import { useWebSocket } from "@/hooks/useWebSocket";

export function AppLayout() {
  useWebSocket(); // Initialize WebSocket connection at layout level

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="min-h-full p-6">
          <Outlet />
        </div>
      </main>
      <SimulatorPanel />
    </div>
  );
}
