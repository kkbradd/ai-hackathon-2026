import { useState, useEffect, useCallback } from "react";
import { fetchShipments, fetchShipmentAlerts } from "../api/client";

export function useShipments() {
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchShipments(statusFilter);
      setShipments(data.shipments);
    } catch (e) {
      setError("Kargo listesi yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    load();
  }, [load]);

  return { shipments, loading, error, statusFilter, setStatusFilter, refresh: load };
}

export function useShipmentAlerts() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchShipmentAlerts();
        setCount(data.count);
      } catch {
        // silent fail — banner just doesn't show
      }
    }
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  return count;
}
