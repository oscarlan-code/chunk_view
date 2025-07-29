"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Signin() {
  const [form, setForm] = useState({ username: "", password: "" });
  const [status, setStatus] = useState<string>("");
  const router = useRouter();

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    const payload = {
      username: form.username,
      password_hash: form.password
    };
    const res = await fetch("http://localhost:8000/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const user = await res.json();
      localStorage.setItem("user", JSON.stringify(user));
      setStatus("Signin successful!");
      router.push("/manager");
    } else {
      setStatus("Signin failed. Check your credentials.");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f5f6fa", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: 'San Francisco, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif' }}>
      <div style={{ background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px rgba(0,0,0,0.08)", padding: 40, minWidth: 340, maxWidth: 400 }}>
        <h2 style={{ fontWeight: 700, fontSize: 28, marginBottom: 24 }}>Manager Sign In</h2>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <input name="username" required placeholder="Username" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} style={{ fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }} />
          <input name="password" required type="password" placeholder="Password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} style={{ fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }} />
          <button type="submit" style={{ background: "#007aff", color: "#fff", border: "none", borderRadius: 8, padding: "12px 0", fontSize: 18, fontWeight: 500, cursor: "pointer", transition: "background 0.2s" }}>Sign In</button>
        </form>
        <div style={{ marginTop: 16, color: status === "Signin successful!" ? "#28a745" : "#d32f2f" }}>{status}</div>
      </div>
    </div>
  );
} 