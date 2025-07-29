"use client";
import { useState } from "react";

export default function Signup() {
  const [form, setForm] = useState({ username: "", role: "manager", password: "" });
  const [status, setStatus] = useState<string>("");

  const handleSubmit = async (e: any) => {
    e.preventDefault();
    const payload = {
      username: form.username,
      role: form.role,
      password_hash: form.password
    };
    const res = await fetch("http://localhost:8000/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      setStatus("Signup successful!");
      setForm({ username: "", role: "manager", password: "" });
    } else {
      setStatus("Signup failed. Try a different username.");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f5f6fa", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: 'San Francisco, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif' }}>
      <div style={{ background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px rgba(0,0,0,0.08)", padding: 40, minWidth: 340, maxWidth: 400 }}>
        <h2 style={{ fontWeight: 700, fontSize: 28, marginBottom: 24 }}>Sign Up</h2>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <input name="username" required placeholder="Username" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} style={{ fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }} />
          <input name="password" required type="password" placeholder="Password" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} style={{ fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }} />
          <select name="role" value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))} style={{ fontSize: 16, padding: 10, borderRadius: 8, border: "1px solid #ddd" }}>
            <option value="manager">Manager</option>
            <option value="operator">Operator</option>
          </select>
          <button type="submit" style={{ background: "#007aff", color: "#fff", border: "none", borderRadius: 8, padding: "12px 0", fontSize: 18, fontWeight: 500, cursor: "pointer", transition: "background 0.2s" }}>Sign Up</button>
        </form>
        <div style={{ marginTop: 16, color: status === "Signup successful!" ? "#28a745" : "#d32f2f" }}>{status}</div>
      </div>
    </div>
  );
} 