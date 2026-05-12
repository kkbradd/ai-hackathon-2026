import { useState, useEffect, useCallback } from "react";
import { fetchDashboard } from "../api/client";

export function useDashboard(weeksAgo = 0) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchDashboard(weeksAgo);
      setData(result);
      setError("");
    } catch (e) {
      setError("Dashboard yüklenemedi.");
    } finally {
      setLoading(false);
    }
  }, [weeksAgo]);

  useEffect(() => {
    load();
    const interval = setInterval(load, 30_000); // 30s — simülasyon verisini canlı yansıt
    return () => clearInterval(interval);
  }, [load]);

  return { data, loading, error, refresh: load };
}
