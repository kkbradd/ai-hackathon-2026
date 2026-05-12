import { useState, useEffect, useCallback } from "react";
import { fetchOrders } from "../api/client";

export function useOrders() {
  const [orders, setOrders] = useState([]);
  const [meta, setMeta] = useState({
    counts_by_status: {},
    pending_pipeline: 0,
    total_matching_filter: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [dateFilter, setDateFilter] = useState("all");
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchOrders(statusFilter, 300, 0, dateFilter);
      setOrders(data.orders);
      setMeta({
        counts_by_status: data.counts_by_status || {},
        pending_pipeline: data.pending_pipeline ?? 0,
        total_matching_filter: data.total_matching_filter ?? 0,
      });
    } catch (err) {
      setError("Siparişler yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, dateFilter]);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = search
    ? orders.filter(
        (o) =>
          o.customer.toLowerCase().includes(search.toLowerCase()) ||
          String(o.order_id).includes(search)
      )
    : orders;

  return {
    orders: filtered,
    meta,
    loading,
    error,
    statusFilter,
    setStatusFilter,
    dateFilter,
    setDateFilter,
    search,
    setSearch,
    refresh: load,
  };
}
