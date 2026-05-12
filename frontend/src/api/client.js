import axios from "axios";

const BASE_URL = "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Redirect to /login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── Auth ──────────────────────────────────────────────────────────────────────
export async function loginRequest(email, password) {
  const res = await api.post("/auth/login", { email, password });
  return res.data;
}

// ── Dashboard ──────────────────────────────────────────────────────────────────
export async function fetchDashboard(weeksAgo = 0) {
  const res = await api.get(`/dashboard?weeks_ago=${weeksAgo}`);
  return res.data;
}

// ── Chat ──────────────────────────────────────────────────────────────────────
export async function sendChat(message, sessionId) {
  const res = await api.post("/chat", { message, session_id: sessionId });
  return res.data;
}

// ── Orders ─────────────────────────────────────────────────────────────────────
export async function fetchOrders(status = "", limit = 50, offset = 0, dateFilter = "") {
  const params = new URLSearchParams();
  if (status) params.append("status", status);
  if (dateFilter) params.append("date_filter", dateFilter);
  params.append("limit", limit);
  params.append("offset", offset);
  const res = await api.get(`/orders?${params.toString()}`);
  return res.data;
}

export async function fetchOrderDetail(orderId) {
  const res = await api.get(`/orders/${orderId}`);
  return res.data;
}

// ── Shipments ──────────────────────────────────────────────────────────────────
export async function fetchShipments(status = "", limit = 300) {
  const params = new URLSearchParams();
  if (status) params.append("status", status);
  params.append("limit", limit);
  const res = await api.get(`/shipments?${params.toString()}`);
  return res.data;
}

export async function fetchShipmentDetail(shipmentId) {
  const res = await api.get(`/shipments/${shipmentId}`);
  return res.data;
}

export async function fetchShipmentAlerts() {
  const res = await api.get("/shipments/alerts");
  return res.data;
}

// ── Inventory ──────────────────────────────────────────────────────────────────
export async function fetchInventory(lowStockOnly = false) {
  const params = lowStockOnly ? "?low_stock_only=true" : "";
  const res = await api.get(`/inventory${params}`);
  return res.data;
}

export async function fetchInventoryAlerts() {
  const res = await api.get("/inventory/alerts");
  return res.data;
}

export async function fetchProductMovements(productId, limit = 20) {
  const res = await api.get(`/inventory/${productId}/movements?limit=${limit}`);
  return res.data;
}

// ── Operational Alerts ─────────────────────────────────────────────────────────
export async function fetchOperationalAlerts(resolved = false) {
  const res = await api.get(`/operational-alerts?resolved=${resolved}`);
  return res.data;
}

export async function resolveAlert(alertId) {
  const res = await api.patch(`/operational-alerts/${alertId}/resolve`);
  return res.data;
}

// ── Analytics ──────────────────────────────────────────────────────────────────
export async function fetchDemandTrends() {
  const res = await api.get("/analytics/demand");
  return res.data;
}

// ── Simulate ───────────────────────────────────────────────────────────────────
export async function triggerSimulationEvent(eventType, targetId = null) {
  const res = await api.post("/simulate/event", {
    event_type: eventType,
    target_id: targetId,
  });
  return res.data;
}

// ── Customer Messages ─────────────────────────────────────────────────────────
export async function fetchMessages(unreadOnly = false) {
  const res = await api.get(`/messages?unread_only=${unreadOnly}`);
  return res.data;
}

export async function markMessageAsRead(messageId) {
  const res = await api.post(`/messages/${messageId}/read`);
  return res.data;
}

export async function fetchMessageCategories() {
  const res = await api.get("/messages/categories");
  return res.data;
}

export async function createMessage(payload) {
  const res = await api.post("/messages", payload);
  return res.data;
}

export async function fetchCustomers() {
  const res = await api.get("/customers");
  return res.data;
}

export default api;
