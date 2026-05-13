import { useState, useEffect, useCallback } from "react";
import { fetchForecast } from "../api/client";

export function useForecast() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async (force = false) => {
    if (force) setRefreshing(true);
    try {
      const result = await fetchForecast(force);
      setData(result);
      setError("");
    } catch {
      setError("Talep tahmini verileri yüklenemedi.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load(false);
  }, [load]);

  return { data, loading, refreshing, error, refresh: () => load(true) };
}
