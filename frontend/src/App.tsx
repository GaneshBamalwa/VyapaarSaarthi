import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppLayout } from "@/layouts/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { OrdersPage } from "@/pages/OrdersPage";
import { ApprovalsPage } from "@/pages/ApprovalsPage";
import { AgentFeedPage } from "@/pages/AgentFeedPage";
import { IntakeAgentPage } from "@/pages/IntakeAgentPage";
import { OCRAgentPage } from "@/pages/OCRAgentPage";
import { SpeechAgentPage } from "@/pages/SpeechAgentPage";
import { CollectionsAgentPage } from "@/pages/CollectionsAgentPage";
import { SimulatorPage } from "@/pages/SimulatorPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/orders" element={<OrdersPage />} />
            <Route path="/approvals" element={<ApprovalsPage />} />
            <Route path="/feed" element={<AgentFeedPage />} />
            <Route path="/agents/intake" element={<IntakeAgentPage />} />
            <Route path="/agents/ocr" element={<OCRAgentPage />} />
            <Route path="/agents/speech" element={<SpeechAgentPage />} />
            <Route path="/agents/collections" element={<CollectionsAgentPage />} />
            <Route path="/simulator" element={<SimulatorPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
