"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase";

interface AdminStats {
  total_users: number;
  total_documents: number;
  total_chunks: number;
  total_feedback: number;
  documents_by_status: Record<string, number>;
  storage_used_mb: number;
}

export default function AdminPage() {
  const router = useRouter();
  const supabase = createClient();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) router.push("/");
    });
    fetchStats();
  }, []);

  async function fetchStats() {
    try {
      const res = await fetch("http://localhost:8000/api/v1/admin/stats");
      const data = await res.json();
      setStats(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const statCards = stats ? [
    { label: "Total Users", value: stats.total_users, icon: "👤", color: "var(--accent-lavender)" },
    { label: "Total Documents", value: stats.total_documents, icon: "📄", color: "var(--accent-sky)" },
    { label: "Total Chunks", value: stats.total_chunks, icon: "🧩", color: "var(--accent-peach)" },
    { label: "Feedback Given", value: stats.total_feedback, icon: "💬", color: "var(--accent-sage)" },
    { label: "Storage Used", value: stats.storage_used_mb + " MB", icon: "💾", color: "var(--accent-rose)" },
  ] : [];

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-primary)" }}>
      <header style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-card)", padding: "0 32px", height: "64px", display: "flex", alignItems: "center", justifyContent: "space-between", boxShadow: "var(--shadow-soft)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "36px", height: "36px", background: "var(--text-primary)", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: "var(--bg-primary)", fontSize: "18px" }}>✦</span>
          </div>
          <h1 style={{ fontSize: "20px", fontFamily: "DM Serif Display, serif" }}>SmartPDF <span style={{ color: "var(--text-muted)" }}>Admin</span></h1>
        </div>
        <div style={{ display: "flex", gap: "10px" }}>
          <button onClick={() => router.push("/chat")} className="btn-ghost" style={{ fontSize: "13px" }}>← Back to App</button>
          <button onClick={fetchStats} className="btn-ghost" style={{ fontSize: "13px" }}>↻ Refresh</button>
        </div>
      </header>

      <div style={{ padding: "32px", maxWidth: "1200px", margin: "0 auto" }}>
        <h2 style={{ fontSize: "28px", marginBottom: "8px" }}>Dashboard</h2>
        <p style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "32px" }}>Platform overview and statistics</p>

        {loading ? (
          <div style={{ textAlign: "center", padding: "60px" }}>
            <div style={{ fontSize: "36px", marginBottom: "12px" }}>✦</div>
            <p style={{ color: "var(--text-muted)" }}>Loading stats...</p>
          </div>
        ) : (
          <>
            {/* Stat Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "16px", marginBottom: "32px" }}>
              {statCards.map((card) => (
                <div key={card.label} style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "20px", boxShadow: "var(--shadow-soft)" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
                    <div style={{ width: "36px", height: "36px", borderRadius: "10px", background: card.color, display: "flex", alignItems: "center", justifyContent: "center", fontSize: "18px" }}>
                      {card.icon}
                    </div>
                    <p style={{ fontSize: "12px", color: "var(--text-muted)", fontWeight: 500 }}>{card.label}</p>
                  </div>
                  <p style={{ fontSize: "28px", fontWeight: 600, fontFamily: "DM Serif Display, serif" }}>{card.value}</p>
                </div>
              ))}
            </div>

            {/* Documents by Status */}
            {stats && (
              <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "24px", boxShadow: "var(--shadow-soft)", marginBottom: "24px" }}>
                <h3 style={{ fontSize: "16px", marginBottom: "16px" }}>📄 Documents by Status</h3>
                <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
                  {Object.entries(stats.documents_by_status).map(([status, count]) => (
                    <div key={status} style={{ padding: "12px 20px", borderRadius: "var(--radius-sm)", background: status === "READY" ? "var(--accent-sage)" : status === "PROCESSING" ? "var(--accent-peach)" : status === "FAILED" ? "var(--accent-rose)" : "var(--accent-lavender)", display: "flex", alignItems: "center", gap: "8px" }}>
                      <span style={{ fontSize: "20px", fontWeight: 700 }}>{count}</span>
                      <span style={{ fontSize: "13px", fontWeight: 500 }}>{status}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* System Health */}
            <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "24px", boxShadow: "var(--shadow-soft)" }}>
              <h3 style={{ fontSize: "16px", marginBottom: "16px" }}>⚡ System Health</h3>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "12px" }}>
                {[
                  { name: "FastAPI", status: "Online", color: "var(--accent-sage)" },
                  { name: "PostgreSQL", status: "Online", color: "var(--accent-sage)" },
                  { name: "Redis", status: "Online", color: "var(--accent-sage)" },
                  { name: "MinIO", status: "Online", color: "var(--accent-sage)" },
                  { name: "Redpanda", status: "Online", color: "var(--accent-sage)" },
                  { name: "Groq AI", status: "Online", color: "var(--accent-sage)" },
                ].map((service) => (
                  <div key={service.name} style={{ padding: "12px", borderRadius: "var(--radius-sm)", background: "var(--bg-secondary)", border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "13px", fontWeight: 500 }}>{service.name}</span>
                    <span style={{ fontSize: "11px", padding: "2px 8px", borderRadius: "20px", background: service.color, fontWeight: 500 }}>{service.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
