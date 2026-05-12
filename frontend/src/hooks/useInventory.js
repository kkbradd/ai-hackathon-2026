import { useState, useEffect, useCallback } from "react";
import { fetchInventory } from "../api/client";

export function useInventory(lowStockOnly = false) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const result = await fetchInventory(lowStockOnly);
      setData(result);
      setError("");
    } catch {
      setError("Envanter verileri yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [lowStockOnly]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, [load]);

  return { data, loading, error, refresh: load };
}
