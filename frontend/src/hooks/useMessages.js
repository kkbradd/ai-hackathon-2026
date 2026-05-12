import { useState, useEffect, useCallback } from "react";
import { fetchMessages, markMessageAsRead } from "../api/client";

export function useMessages() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await fetchMessages();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message || "Mesajlar yüklenirken bir hata oluştu");
    } finally {
      setLoading(false);
    }
  }, []);

  const markAsRead = async (id) => {
    try {
      await markMessageAsRead(id);
      setData(prev => {
        if (!prev) return prev;
        const target = prev.messages.find((m) => m.id === id);
        const wasUnreadInbound =
          target && target.direction === "inbound" && !target.is_read;
        const nextUnread = Math.max(
          0,
          (prev.stats?.unread_inbound ?? 0) - (wasUnreadInbound ? 1 : 0)
        );
        return {
          ...prev,
          messages: prev.messages.map((m) =>
            m.id === id ? { ...m, is_read: true } : m
          ),
          stats: prev.stats
            ? { ...prev.stats, unread_inbound: nextUnread }
            : prev.stats,
        };
      });
    } catch (err) {
      console.error("Error marking message as read:", err);
    }
  };

  useEffect(() => {refresh();}, [refresh]);

  return { data, loading, error, refresh, markAsRead };
}
