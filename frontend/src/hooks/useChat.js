import { useState, useRef } from "react";
import { sendChat } from "../api/client";
import { sanitizeChatText } from "../utils/sanitizeChatText";

export function useChat() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "Merhaba! Ben **Tarım ve Gıda Kooperatifi** AI Operasyon Asistanınım.\n\nSipariş yönetimi, kargo takibi, **stok uyarıları**, talep trendleri ve kapsamlı operasyon raporları için sorularınızı sorabilirsiniz.\n\nProaktif olarak çalışıyorum — kritik durumları siz sormadan önce tespit ederim.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [loading, setLoading] = useState(false);
  const sessionId = useRef(`session_${Date.now()}`);

  async function sendMessage(text) {
    if (!text.trim() || loading) return;

    const userMsg = { role: "user", text, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const data = await sendChat(text, sessionId.current);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: sanitizeChatText(data.reply || ""),
          toolUsed: data.tool_used,
          toolData: data.tool_data,
          timestamp: new Date().toISOString(),
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: "Bir hata oluştu. Lütfen tekrar deneyin.",
          isError: true,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return { messages, loading, sendMessage };
}
