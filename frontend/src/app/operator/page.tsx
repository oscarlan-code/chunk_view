import Link from "next/link";

export default function OperatorDashboard() {
  return (
    <div style={{ minHeight: "100vh", background: "#f5f6fa", display: "flex", alignItems: "center", justifyContent: "center", fontFamily: 'San Francisco, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica Neue, Arial, sans-serif' }}>
      <div style={{ background: "#fff", borderRadius: 16, boxShadow: "0 4px 24px rgba(0,0,0,0.08)", padding: 40, minWidth: 340, textAlign: "center" }}>
        <h1 style={{ fontWeight: 700, fontSize: 32, marginBottom: 24 }}>Operator Dashboard</h1>
        <ul style={{ fontSize: 18, listStyle: "none", padding: 0, marginBottom: 32 }}>
          <li style={{ margin: "16px 0" }}>
            <Link href="/operator/troubleshoot" style={{ textDecoration: "none", color: "#007aff", fontWeight: 500, padding: "12px 24px", borderRadius: 8, background: "#f0f4ff", transition: "background 0.2s" }}>Start Troubleshooting</Link>
          </li>
          <li style={{ margin: "16px 0" }}>
            <Link href="/operator/machines" style={{ textDecoration: "none", color: "#007aff", fontWeight: 500, padding: "12px 24px", borderRadius: 8, background: "#f0f4ff", transition: "background 0.2s" }}>Machine Dashboard</Link>
          </li>
          <li style={{ margin: "16px 0" }}>
            <Link href="/operator/reports" style={{ textDecoration: "none", color: "#007aff", fontWeight: 500, padding: "12px 24px", borderRadius: 8, background: "#f0f4ff", transition: "background 0.2s" }}>View Reports</Link>
          </li>
        </ul>
        <Link href="/" style={{ color: "#888", fontSize: 16 }}>Back to Role Selection</Link>
      </div>
    </div>
  );
} 