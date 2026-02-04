import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import AutomationPage from "./pages/AutomationPage";
import PreviewPage from "./pages/PreviewPage";
import StandardsPage from "./pages/StandardsPage";
import ValidationPage from "./pages/ValidationPage";
import ApprovalPage from "./pages/ApprovalPage";
import DatasheetGeneratorPage from "./pages/DatasheetGeneratorPage";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/automation" element={<AutomationPage />} />
            <Route path="/preview" element={<PreviewPage />} />
            <Route path="/standards" element={<StandardsPage />} />
            <Route path="/validation" element={<ValidationPage />} />
            <Route path="/approval" element={<ApprovalPage />} />
            <Route path="/generator" element={<DatasheetGeneratorPage />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
