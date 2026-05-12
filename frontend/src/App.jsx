import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./store/authStore";
import ProtectedLayout from "./components/layout/ProtectedLayout";
import LoginPage from "./pages/LoginPage";
import DashboardPanel from "./components/dashboard/DashboardPanel";
import ChatPanel from "./components/chat/ChatPanel";
import OrdersPanel from "./components/orders/OrdersPanel";
import ShipmentsPanel from "./components/shipments/ShipmentsPanel";
import InventoryPage from "./pages/InventoryPage";
import MessagesPage from "./pages/MessagesPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<ProtectedLayout />}>
            <Route path="/" element={<DashboardPanel />} />
            <Route path="/chat" element={<ChatPanel />} />
            <Route path="/orders" element={<OrdersPanel />} />
            <Route path="/shipments" element={<ShipmentsPanel />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/messages" element={<MessagesPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
