"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const [role, setRole] = useState<string | null>(null);
  const router = useRouter();

  const handleSelect = (selectedRole: string) => {
    setRole(selectedRole);
    if (selectedRole === "manager") {
      router.push("/manager");
    } else if (selectedRole === "operator") {
      router.push("/operator");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f5f6fa", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: 'San Francisco, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif' }}>
      <div style={{ background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px rgba(0,0,0,0.08)", padding: 40, minWidth: 340, textAlign: "center" }}>
        <h1 style={{ fontWeight: 700, fontSize: 32, marginBottom: 16 }}>Welcome to upskill</h1>
        <p style={{ color: "#666", fontSize: 18, marginBottom: 32 }}>Select your role to continue:</p>
        <div style={{ display: "flex", gap: 32, justifyContent: "center" }}>
          <button
            onClick={() => handleSelect("manager")}
            style={{
              padding: "18px 36px",
              fontSize: 20,
              fontWeight: 600,
              borderRadius: 12,
              border: "none",
              background: "#f0f4ff",
              color: "#007aff",
              cursor: "pointer",
              boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
              transition: "background 0.2s, color 0.2s",
            }}
            onMouseOver={e => (e.currentTarget.style.background = '#e6eeff')}
            onMouseOut={e => (e.currentTarget.style.background = '#f0f4ff')}
          >
            Manager
          </button>
          <button
            onClick={() => handleSelect("operator")}
            style={{
              padding: "18px 36px",
              fontSize: 20,
              fontWeight: 600,
              borderRadius: 12,
              border: "none",
              background: "#f0f4ff",
              color: "#007aff",
              cursor: "pointer",
              boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
              transition: "background 0.2s, color 0.2s",
            }}
            onMouseOver={e => (e.currentTarget.style.background = '#e6eeff')}
            onMouseOut={e => (e.currentTarget.style.background = '#f0f4ff')}
          >
            Operator
          </button>
        </div>
      </div>
    </div>
  );
}
