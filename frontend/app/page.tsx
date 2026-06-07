"use client";

import { useState } from "react";
import { createClient } from "@/lib/supabase";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const supabase = createClient();

  async function handleGoogleLogin() {
    setLoading(true);
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: window.location.origin + "/dashboard" },
    });
  }

  async function handleMagicLink() {
    if (!email.trim()) return;
    setLoading(true);
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: window.location.origin + "/dashboard" },
    });
    setLoading(false);
    if (!error) setSent(true);
  }

  return (
    <div style={{
      minHeight: "100vh",
      background: "var(--bg-primary)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "24px",
      position: "relative",
      overflow: "hidden",
    }}>
      {/* Background blobs */}
      <div style={{
        position: "absolute", top: "-100px", right: "-100px",
        width: "500px", height: "500px", borderRadius: "50%",
        background: "radial-gradient(circle, rgba(184,212,200,0.3) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />
      <div style={{
        position: "absolute", bottom: "-100px", left: "-100px",
        width: "400px", height: "400px", borderRadius: "50%",
        background: "radial-gradient(circle, rgba(200,192,216,0.3) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />
      <div style={{
        position: "absolute", top: "40%", left: "20%",
        width: "300px", height: "300px", borderRadius: "50%",
        background: "radial-gradient(circle, rgba(240,200,168,0.2) 0%, transparent 70%)",
        pointerEvents: "none",
      }} />

      <div style={{
        width: "100%", maxWidth: "420px",
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: "var(--radius-lg)",
        boxShadow: "var(--shadow-strong)",
        padding: "48px 40px",
        position: "relative",
        zIndex: 1,
      }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: "40px" }}>
          <div style={{
            width: "56px", height: "56px",
            background: "var(--text-primary)",
            borderRadius: "16px",
            display: "flex", alignItems: "center", justifyContent: "center",
            margin: "0 auto 16px",
            boxShadow: "0 8px 24px rgba(44,36,32,0.2)",
          }}>
            <span style={{ color: "var(--bg-primary)", fontSize: "26px" }}>✦</span>
          </div>
          <h1 style={{ fontSize: "28px", marginBottom: "6px", fontFamily: "DM Serif Display, serif" }}>
            SmartPDF <span style={{ fontStyle: "italic", color: "var(--text-muted)" }}>AI</span>
          </h1>
          <p style={{ fontSize: "14px", color: "var(--text-muted)" }}>
            Your intelligent document companion
          </p>
        </div>

        {/* Feature pills */}
        <div style={{ display: "flex", gap: "8px", justifyContent: "center", marginBottom: "36px", flexWrap: "wrap" }}>
          {["📄 PDF Chat", "🧠 AI Search", "📌 Notes", "🎯 Citations"].map((f) => (
            <span key={f} style={{
              fontSize: "11px", padding: "4px 10px",
              borderRadius: "20px", background: "var(--bg-secondary)",
              border: "1px solid var(--border)", color: "var(--text-secondary)",
              fontWeight: 500,
            }}>
              {f}
            </span>
          ))}
        </div>

        {sent ? (
          <div style={{
            textAlign: "center", padding: "24px",
            background: "var(--bg-secondary)",
            borderRadius: "var(--radius)",
            border: "1px solid var(--border)",
          }}>
            <div style={{ fontSize: "36px", marginBottom: "12px" }}>📬</div>
            <p style={{ fontWeight: 500, marginBottom: "6px" }}>Check your email!</p>
            <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>
              We sent a magic link to <strong>{email}</strong>
            </p>
          </div>
        ) : (
          <>
            {/* Google Login */}
            <button
              onClick={handleGoogleLogin}
              disabled={loading}
              style={{
                width: "100%", padding: "13px",
                borderRadius: "var(--radius-sm)",
                border: "1px solid var(--border)",
                background: "white",
                cursor: "pointer",
                display: "flex", alignItems: "center", justifyContent: "center", gap: "10px",
                fontSize: "14px", fontWeight: 500,
                fontFamily: "DM Sans, sans-serif",
                transition: "all 0.2s",
                boxShadow: "var(--shadow-soft)",
                marginBottom: "16px",
              }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
              </svg>
              Continue with Google
            </button>

            {/* Divider */}
            <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "16px" }}>
              <div style={{ flex: 1, height: "1px", background: "var(--border)" }} />
              <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>or continue with email</span>
              <div style={{ flex: 1, height: "1px", background: "var(--border)" }} />
            </div>

            {/* Email Magic Link */}
            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
              <input
                type="email"
                placeholder="your@email.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleMagicLink()}
                style={{
                  width: "100%", padding: "12px 16px",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border)",
                  background: "var(--bg-primary)",
                  fontSize: "14px", outline: "none",
                  fontFamily: "DM Sans, sans-serif",
                  color: "var(--text-primary)",
                  transition: "border-color 0.2s",
                }}
              />
              <button
                onClick={handleMagicLink}
                disabled={loading || !email.trim()}
                className="btn-primary"
                style={{ width: "100%", padding: "12px", fontSize: "14px" }}
              >
                {loading ? "Sending..." : "Send Magic Link ✦"}
              </button>
            </div>
          </>
        )}

        <p style={{ textAlign: "center", fontSize: "11px", color: "var(--text-muted)", marginTop: "28px" }}>
          By signing in, you agree to our Terms of Service
        </p>
      </div>
    </div>
  );
}
