"use client";
import { useState } from "react";

export default function Troubleshoot() {
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [chat, setChat] = useState<{ sender: string; message: string }[]>([]);
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("");

  const startSession = async () => {
    const res = await fetch("http://localhost:8000/sessions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operator_id: 2 })
    });
    if (res.ok) {
      const data = await res.json();
      setSessionId(data.id);
      setChat([]);
      setStatus("Session started");
    } else {
      setStatus("Failed to start session");
    }
  };

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input || !sessionId) return;
    setChat(prev => [...prev, { sender: "You", message: input }]);
    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ query: input })
    });
    if (res.ok) {
      const data = await res.json();
      setChat(prev => [...prev, { sender: "Agent", message: data.response }]);
      setInput("");
    } else {
      setStatus("Chat failed");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f5f6fa", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: 'San Francisco, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif' }}>
      <div style={{ background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px rgba(0,0,0,0.08)", padding: 40, minWidth: 340, maxWidth: 500 }}>
        <h2 style={{ fontWeight: 700, fontSize: 28, marginBottom: 24 }}>Troubleshooting Chat</h2>
        {!sessionId ? (
          <button onClick={startSession} style={{ background: "#007aff", color: "#fff", border: "none", borderRadius: 8, padding: "12px 0", fontSize: 18, fontWeight: 500, cursor: "pointer", width: "100%", marginBottom: 16 }}>Start Session</button>
        ) : (
          <>
            <div style={{ border: "1px solid #e0e0e0", borderRadius: 8, padding: 16, minHeight: 200, background: "#f8faff", marginBottom: 16, maxHeight: 300, overflowY: "auto" }}>
              {chat.map((msg, i) => (
                <div key={i} style={{ marginBottom: 8, textAlign: msg.sender === "You" ? "right" : "left" }}>
                  <span style={{ display: "inline-block", background: msg.sender === "You" ? "#007aff" : "#e5e5ea", color: msg.sender === "You" ? "#fff" : "#222", borderRadius: 16, padding: "8px 16px", maxWidth: "80%", fontSize: 16 }}>{msg.message}</span>
                </div>
              ))}
            </div>
            <form onSubmit={sendMessage} style={{ display: "flex", gap: 8 }}>
              <input value={input} onChange={e => setInput(e.target.value)} style={{ flex: 1, fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }} />
              <button type="submit" style={{ background: "#007aff", color: "#fff", border: "none", borderRadius: 8, padding: "0 24px", fontSize: 16, fontWeight: 500, cursor: "pointer", transition: "background 0.2s" }}>Send</button>
            </form>
          </>
        )}
        <div style={{ color: status === "Session started" ? "#28a745" : "#d32f2f", marginTop: 16 }}>{status}</div>
      </div>
    </div>
  );
} 