import { useState, useEffect, useCallback, useRef } from "react";
import { fetchInsights, dismissInsight } from "../api/client";

const POLL_INTERVAL = 60_000; // 60 seconds

export default function useInsights(params = {}) {
  const [insights, setInsights] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const paramsRef = useRef(params);

  const load = useCallback(async () => {
    try {
      const data = await fetchInsights(paramsRef.current);
      setInsights(data.items || []);
      setError(null);
    } catch (e) {
      setError(e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, POLL_INTERVAL);
    return () => clearInterval(id);
  }, [load]);

  const dismiss = useCallback(async (id) => {
    setInsights((prev) => prev.filter((i) => i.id !== id));
    try {
      await dismissInsight(id);
    } catch {
      // pessimistic rollback not needed — insight is just hidden
    }
  }, []);

  return { insights, loading, error, dismiss, refresh: load };
}
