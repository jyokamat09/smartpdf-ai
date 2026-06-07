"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase";
import { uploadDocument, listDocuments, askQuestion, submitFeedback, sendNotesEmail as sendNotesEmail_api } from "@/lib/api";
import QuizPanel from "@/app/components/QuizPanel";

interface DocItem {
  id: string;
  name: string;
  status: string;
  file_type: string;
  file_size: number;
  chunk_count: number | null;
  page_count: number | null;
}

interface Citation {
  chunk_id: string;
  chunk_index: number;
  page_number: number | null;
  document_id: string;
  similarity: number;
  excerpt: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  question?: string;
  citations?: Citation[];
  tokens?: number;
  confidence?: number;
  feedback?: "thumbs_up" | "thumbs_down";
  saved?: boolean;
}

interface Note {
  id: string;
  content: string;
  docName: string;
  savedAt: string;
}

const WORKSPACE_ID = "2e0288cc-39b3-430b-9602-3e7c49a5640b";
const USER_ID = "2e0288cc-39b3-430b-9602-3e7c49a5640b";

export default function ChatPage() {
  const router = useRouter();
  const supabase = createClient();
  const [user, setUser] = useState<any>(null);
  const [documents, setDocuments] = useState<DocItem[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocItem | null>(null);
  const [chatHistories, setChatHistories] = useState<Record<string, Message[]>>({});
  const [question, setQuestion] = useState("");
  const [uploading, setUploading] = useState(false);
  const [asking, setAsking] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [notes, setNotes] = useState<Note[]>([]);
  const [showNotes, setShowNotes] = useState(false);
  const [showQuiz, setShowQuiz] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [emailModal, setEmailModal] = useState(false);
  const [emailAddr, setEmailAddr] = useState("");
  const [emailSending, setEmailSending] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const chatKey = selectedDoc ? selectedDoc.id : "global";
  const messages = chatHistories[chatKey] || [];

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!session) router.push("/");
      else { setUser(session.user); setEmailAddr(session.user.email || ""); }
    });
    fetchDocuments();
    const saved = localStorage.getItem("smartpdf_notes");
    if (saved) setNotes(JSON.parse(saved));
  }, []);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function fetchDocuments() {
    try {
      const data = await listDocuments(WORKSPACE_ID);
      setDocuments(data.documents || []);
    } catch (e) { console.error(e); }
  }

  async function handleUpload(file: File) {
    setUploading(true);
    try { await uploadDocument(file, WORKSPACE_ID, USER_ID); await fetchDocuments(); }
    catch (e) { alert("Upload failed."); }
    finally { setUploading(false); }
  }

  function updateMessage(msgId: string, updates: Partial<Message>) {
    setChatHistories((prev) => ({
      ...prev,
      [chatKey]: (prev[chatKey] || []).map((m) => m.id === msgId ? { ...m, ...updates } : m),
    }));
  }

  async function handleFeedback(msg: Message, type: "thumbs_up" | "thumbs_down") {
    updateMessage(msg.id, { feedback: type });
    try {
      const chunkIds = msg.citations?.map((c) => c.chunk_id).filter(Boolean) || [];
      await submitFeedback(type, msg.question || "", msg.content, WORKSPACE_ID, chunkIds, selectedDoc?.id);
    } catch (e) { console.error("Feedback error:", e); }
  }

  function handleSaveNote(msg: Message) {
    const note: Note = {
      id: Date.now().toString(),
      content: msg.content,
      docName: selectedDoc?.name || "General",
      savedAt: new Date().toLocaleString(),
    };
    const updated = [note, ...notes];
    setNotes(updated);
    localStorage.setItem("smartpdf_notes", JSON.stringify(updated));
    updateMessage(msg.id, { saved: true });
  }

  function handleCopy(msg: Message) {
    navigator.clipboard.writeText(msg.content);
    setCopiedId(msg.id);
    setTimeout(() => setCopiedId(null), 2000);
  }

  function handleRegenerate(msg: Message) {
    if (msg.question) setQuestion(msg.question);
  }

  function deleteNote(id: string) {
    const updated = notes.filter((n) => n.id !== id);
    setNotes(updated);
    localStorage.setItem("smartpdf_notes", JSON.stringify(updated));
  }

  function downloadNotesPDF() {
    const content = notes.map((n, i) =>
      `Note ${i + 1} - ${n.docName}\nSaved: ${n.savedAt}\n\n${n.content}\n\n${"=".repeat(50)}\n`
    ).join("\n");

    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "smartpdf-notes.txt";
    a.click();
    URL.revokeObjectURL(url);
  }

  async function sendNotesEmail() {
    if (!emailAddr.trim()) return;
    setEmailSending(true);
    try {
      await sendNotesEmail_api(emailAddr, notes);
      setEmailSent(true);
      setTimeout(() => { setEmailSent(false); setEmailModal(false); }, 2000);
    } catch (e) {
      alert("Failed to send email. Please try again.");
    } finally {
      setEmailSending(false);
    }
  }

  async function handleAsk(overrideQuestion?: string) {
    const q = overrideQuestion || question;
    if (!q.trim() || asking) return;
    const userMsg: Message = { id: Date.now().toString(), role: "user", content: q };
    setChatHistories((prev) => ({ ...prev, [chatKey]: [...(prev[chatKey] || []), userMsg] }));
    setQuestion("");
    setAsking(true);
    try {
      const data = await askQuestion(q, WORKSPACE_ID, selectedDoc?.id);
      setChatHistories((prev) => ({ ...prev, [chatKey]: [...(prev[chatKey] || []), {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.answer,
        question: q,
        citations: data.citations,
        tokens: data.tokens_used,
        confidence: data.confidence,
      }]}));
    } catch (e) {
      setChatHistories((prev) => ({ ...prev, [chatKey]: [...(prev[chatKey] || []), {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I could not answer that. Please try again.",
        question: q,
      }]}));
    } finally { setAsking(false); }
  }

  async function handleLogout() { await supabase.auth.signOut(); router.push("/"); }

  function formatSize(bytes: number) {
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  function getStatusColor(status: string) {
    if (status === "READY") return "var(--accent-sage)";
    if (status === "PROCESSING") return "var(--accent-peach)";
    if (status === "FAILED") return "var(--accent-rose)";
    return "var(--accent-lavender)";
  }

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg-primary)" }}>
      {/* Email Modal */}
      {emailModal && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(44,36,32,0.4)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", padding: "32px", width: "360px", boxShadow: "var(--shadow-strong)" }}>
            <h3 style={{ fontSize: "18px", marginBottom: "8px" }}>📧 Email Notes</h3>
            <p style={{ fontSize: "13px", color: "var(--text-muted)", marginBottom: "20px" }}>Send your {notes.length} notes to your email.</p>
            {emailSent ? (
              <div style={{ textAlign: "center", padding: "16px" }}>
                <div style={{ fontSize: "32px", marginBottom: "8px" }}>✅</div>
                <p style={{ fontWeight: 500 }}>Email sent!</p>
              </div>
            ) : (
              <>
                <input
                  type="email"
                  value={emailAddr}
                  onChange={(e) => setEmailAddr(e.target.value)}
                  placeholder="your@email.com"
                  style={{ width: "100%", padding: "10px 14px", borderRadius: "var(--radius-sm)", border: "1px solid var(--border)", background: "var(--bg-primary)", fontSize: "14px", outline: "none", marginBottom: "12px", fontFamily: "DM Sans, sans-serif" }}
                />
                <div style={{ display: "flex", gap: "8px" }}>
                  <button onClick={() => setEmailModal(false)} className="btn-ghost" style={{ flex: 1 }}>Cancel</button>
                  <button onClick={sendNotesEmail} disabled={emailSending} className="btn-primary" style={{ flex: 1 }}>
                    {emailSending ? "Sending..." : "Send ✦"}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      <header style={{ borderBottom: "1px solid var(--border)", background: "var(--bg-card)", padding: "0 32px", height: "64px", display: "flex", alignItems: "center", justifyContent: "space-between", boxShadow: "var(--shadow-soft)", position: "sticky", top: 0, zIndex: 100 }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div style={{ width: "36px", height: "36px", background: "var(--text-primary)", borderRadius: "10px", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <span style={{ color: "var(--bg-primary)", fontSize: "18px" }}>✦</span>
          </div>
          <h1 style={{ fontSize: "20px", fontFamily: "DM Serif Display, serif" }}>SmartPDF <span style={{ color: "var(--text-muted)" }}>AI</span></h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          {(selectedDoc && (selectedDoc.status === "READY" || selectedDoc.status === "ready")) && (
            <button onClick={() => setShowQuiz(true)} style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "6px 12px", fontSize: "13px", cursor: "pointer" }}>🧪 Quiz</button>
          )}
          <button onClick={() => setShowNotes(!showNotes)} style={{ background: showNotes ? "var(--accent-lavender)" : "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "6px 12px", fontSize: "13px", cursor: "pointer", display: "flex", alignItems: "center", gap: "6px" }}>
            📌 Notes {notes.length > 0 && <span style={{ background: "var(--text-primary)", color: "var(--bg-primary)", borderRadius: "10px", padding: "0 6px", fontSize: "11px" }}>{notes.length}</span>}
          </button>
          {user && <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>{user.email}</span>}
          <button onClick={() => router.push("/admin")} className="btn-ghost" style={{ fontSize: "13px" }}>📊 Admin</button>
          <button onClick={handleLogout} className="btn-ghost" style={{ fontSize: "13px" }}>Sign out</button>
        </div>
      </header>

      <div style={{ display: "flex", height: "calc(100vh - 64px)" }}>
        <aside style={{ width: "280px", borderRight: "1px solid var(--border)", background: "var(--bg-card)", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "16px" }}>
            <div onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)} onDrop={(e) => { e.preventDefault(); setDragOver(false); const f = e.dataTransfer.files[0]; if (f) handleUpload(f); }} onClick={() => fileInputRef.current?.click()} style={{ border: "2px dashed " + (dragOver ? "var(--text-primary)" : "var(--border)"), borderRadius: "var(--radius)", padding: "20px 12px", textAlign: "center", cursor: "pointer", background: dragOver ? "var(--bg-secondary)" : "transparent", transition: "all 0.2s" }}>
              <div style={{ fontSize: "24px", marginBottom: "6px" }}>{uploading ? "⏳" : "📄"}</div>
              <p style={{ fontSize: "12px", fontWeight: 500 }}>{uploading ? "Uploading..." : "Drop file or click"}</p>
              <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>PDF · DOCX · PPTX · TXT</p>
            </div>
            <input ref={fileInputRef} type="file" accept=".pdf,.docx,.pptx,.txt,.md" style={{ display: "none" }} onChange={(e) => { const f = e.target.files?.[0]; if (f) handleUpload(f); }} />
          </div>

          <div style={{ padding: "0 16px 6px" }}>
            <p style={{ fontSize: "10px", fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.1em" }}>CHATS</p>
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: "0 8px 8px" }}>
            <div onClick={() => setSelectedDoc(null)} style={{ padding: "10px", borderRadius: "var(--radius-sm)", cursor: "pointer", marginBottom: "3px", border: "1px solid " + (!selectedDoc ? "var(--border-hover)" : "transparent"), background: !selectedDoc ? "var(--bg-secondary)" : "transparent", display: "flex", alignItems: "center", gap: "8px" }}>
              <span>🌐</span>
              <div style={{ flex: 1 }}>
                <p style={{ fontSize: "13px", fontWeight: 500 }}>All Documents</p>
                {(chatHistories["global"] || []).length > 0 && <p style={{ fontSize: "11px", color: "var(--text-muted)" }}>{(chatHistories["global"] || []).filter(m => m.role === "user").length} messages</p>}
              </div>
            </div>
            {documents.map((doc) => (
              <div key={doc.id} onClick={() => setSelectedDoc(doc)} style={{ padding: "10px", borderRadius: "var(--radius-sm)", cursor: "pointer", marginBottom: "3px", border: "1px solid " + (selectedDoc?.id === doc.id ? "var(--border-hover)" : "transparent"), background: selectedDoc?.id === doc.id ? "var(--bg-secondary)" : "transparent", transition: "all 0.15s" }}>
                <div style={{ display: "flex", alignItems: "flex-start", gap: "8px" }}>
                  <span style={{ fontSize: "16px" }}>{doc.file_type === "pdf" ? "📕" : doc.file_type === "docx" ? "📘" : "📗"}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ fontSize: "12px", fontWeight: 500, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{doc.name}</p>
                    <div style={{ display: "flex", gap: "4px", marginTop: "3px" }}>
                      <span style={{ fontSize: "10px", padding: "1px 6px", borderRadius: "20px", background: getStatusColor(doc.status) }}>{doc.status}</span>
                      {(chatHistories[doc.id] || []).filter(m => m.role === "user").length > 0 && <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>{(chatHistories[doc.id] || []).filter(m => m.role === "user").length} msgs</span>}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ padding: "10px", borderTop: "1px solid var(--border)" }}>
            <button className="btn-ghost" style={{ width: "100%", fontSize: "12px" }} onClick={fetchDocuments}>↻ Refresh</button>
          </div>
        </aside>

        <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
          <div style={{ padding: "10px 24px", borderBottom: "1px solid var(--border)", background: "var(--bg-card)", display: "flex", alignItems: "center", gap: "10px" }}>
            {selectedDoc ? (
              <>
                <span>{selectedDoc.file_type === "pdf" ? "📕" : "📘"}</span>
                <span style={{ fontSize: "13px", fontWeight: 500 }}>{selectedDoc.name}</span>
                <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>· {selectedDoc.chunk_count || 0} chunks</span>
                <button onClick={() => setSelectedDoc(null)} style={{ marginLeft: "auto", fontSize: "12px", color: "var(--text-muted)", background: "none", border: "none", cursor: "pointer" }}>✕ Clear</button>
              </>
            ) : (
              <span style={{ fontSize: "13px", color: "var(--text-muted)" }}>🌐 All documents · click a doc to focus</span>
            )}
          </div>

          <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
            {messages.length === 0 ? (
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "100%", gap: "16px" }}>
                <div style={{ fontSize: "48px" }}>✦</div>
                <h2 style={{ fontSize: "22px" }}>{selectedDoc ? "Chat with " + selectedDoc.name : "Ask anything"}</h2>
                <p style={{ fontSize: "14px", color: "var(--text-muted)", textAlign: "center", maxWidth: "380px" }}>
                  {selectedDoc ? "Ask questions and get AI answers with citations." : "Select a document or ask across all documents."}
                </p>
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "center" }}>
                  {["What is this about?", "Summarize key points", "List main concepts"].map((s) => (
                    <button key={s} onClick={() => handleAsk(s)} style={{ padding: "7px 14px", borderRadius: "20px", border: "1px solid var(--border)", background: "var(--bg-card)", fontSize: "12px", cursor: "pointer", color: "var(--text-secondary)" }}>{s}</button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="animate-fade-in" style={{ marginBottom: "20px", display: "flex", flexDirection: msg.role === "user" ? "row-reverse" : "row", gap: "10px", alignItems: "flex-start" }}>
                  <div style={{ width: "30px", height: "30px", borderRadius: "50%", background: msg.role === "user" ? "var(--accent-lavender)" : "var(--text-primary)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontSize: "13px" }}>
                    {msg.role === "user" ? "👤" : "✦"}
                  </div>
                  <div style={{ maxWidth: "72%" }}>
                    <div style={{ padding: "12px 16px", borderRadius: msg.role === "user" ? "16px 4px 16px 16px" : "4px 16px 16px 16px", background: msg.role === "user" ? "var(--text-primary)" : "var(--bg-card)", color: msg.role === "user" ? "var(--bg-primary)" : "var(--text-primary)", border: msg.role === "assistant" ? "1px solid var(--border)" : "none", fontSize: "14px", lineHeight: "1.7", boxShadow: "var(--shadow-soft)" }}>
                      {msg.content}
                    </div>
                    {msg.role === "assistant" && msg.confidence !== undefined && (
                      <div style={{ display: "inline-flex", alignItems: "center", gap: "6px", marginTop: "6px", padding: "3px 10px", borderRadius: "20px", background: msg.confidence >= 70 ? "var(--accent-sage)" : msg.confidence >= 40 ? "var(--accent-peach)" : "var(--accent-rose)", fontSize: "11px", fontWeight: 500 }}>
                        🎯 {msg.confidence}% confident
                      </div>
                    )}
                    {msg.role === "assistant" && (
                      <div style={{ display: "flex", gap: "5px", marginTop: "6px", flexWrap: "wrap" }}>
                        {[
                          { icon: msg.feedback === "thumbs_up" ? "👍✓" : "👍", label: "Good answer", color: msg.feedback === "thumbs_up" ? "var(--accent-sage)" : "var(--bg-secondary)", action: () => handleFeedback(msg, "thumbs_up") },
                          { icon: msg.feedback === "thumbs_down" ? "👎✓" : "👎", label: "Bad answer", color: msg.feedback === "thumbs_down" ? "var(--accent-rose)" : "var(--bg-secondary)", action: () => handleFeedback(msg, "thumbs_down") },
                          { icon: copiedId === msg.id ? "✓ Copied" : "📋 Copy", label: "Copy", color: copiedId === msg.id ? "var(--accent-sage)" : "var(--bg-secondary)", action: () => handleCopy(msg) },
                          { icon: msg.saved ? "📌 Saved" : "📌 Save", label: "Save to notes", color: msg.saved ? "var(--accent-lavender)" : "var(--bg-secondary)", action: () => handleSaveNote(msg) },
                          { icon: "🔄 Retry", label: "Regenerate", color: "var(--bg-secondary)", action: () => handleRegenerate(msg) },
                        ].map((btn) => (
                          <button key={btn.label} onClick={btn.action} title={btn.label} style={{ background: btn.color, border: "1px solid var(--border)", borderRadius: "8px", padding: "4px 10px", fontSize: "12px", cursor: "pointer", transition: "all 0.15s", fontFamily: "DM Sans, sans-serif" }}>
                            {btn.icon}
                          </button>
                        ))}
                      </div>
                    )}
                    {msg.citations && msg.citations.length > 0 && (
                      <div style={{ marginTop: "8px" }}>
                        <p style={{ fontSize: "10px", color: "var(--text-muted)", marginBottom: "5px", fontWeight: 600, letterSpacing: "0.05em" }}>SOURCES</p>
                        {msg.citations.slice(0, 3).map((c, i) => (
                          <div key={i} style={{ padding: "8px 12px", borderRadius: "var(--radius-sm)", background: "var(--bg-secondary)", border: "1px solid var(--border)", fontSize: "12px", marginBottom: "5px" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "3px" }}>
                              <span style={{ fontWeight: 500, color: "var(--text-secondary)" }}>Chunk {c.chunk_index + 1}{c.page_number ? " · Page " + c.page_number : ""}</span>
                              <span style={{ background: "var(--accent-sage)", padding: "1px 7px", borderRadius: "10px", fontSize: "10px" }}>{(c.similarity * 100).toFixed(0)}%</span>
                            </div>
                            <p style={{ color: "var(--text-muted)", lineHeight: "1.5" }}>{c.excerpt.substring(0, 100)}...</p>
                          </div>
                        ))}
                        {msg.tokens && <p style={{ fontSize: "10px", color: "var(--text-muted)" }}>{msg.tokens} tokens used</p>}
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {asking && (
              <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                <div style={{ width: "30px", height: "30px", borderRadius: "50%", background: "var(--text-primary)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "13px" }}>✦</div>
                <div style={{ padding: "12px 16px", borderRadius: "4px 16px 16px 16px", background: "var(--bg-card)", border: "1px solid var(--border)", display: "flex", gap: "5px", alignItems: "center" }}>
                  {[0, 1, 2].map((i) => (<div key={i} style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--text-muted)", animation: "pulse-soft 1.2s ease " + (i * 0.2) + "s infinite" }} />))}
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          <div style={{ padding: "14px 24px", borderTop: "1px solid var(--border)", background: "var(--bg-card)" }}>
            <div style={{ display: "flex", gap: "10px", background: "var(--bg-primary)", border: "1px solid var(--border)", borderRadius: "var(--radius)", padding: "8px 8px 8px 16px", boxShadow: "var(--shadow-soft)" }}>
              <input value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) handleAsk(); }} placeholder={selectedDoc ? "Ask about " + selectedDoc.name + "..." : "Ask anything..."} style={{ flex: 1, border: "none", outline: "none", background: "transparent", fontSize: "14px", color: "var(--text-primary)", fontFamily: "DM Sans, sans-serif" }} />
              <button onClick={() => handleAsk()} disabled={!question.trim() || asking} style={{ background: question.trim() ? "var(--text-primary)" : "var(--border)", color: question.trim() ? "var(--bg-primary)" : "var(--text-muted)", border: "none", borderRadius: "10px", width: "36px", height: "36px", cursor: question.trim() ? "pointer" : "default", fontSize: "16px", transition: "all 0.2s", display: "flex", alignItems: "center", justifyContent: "center" }}>↑</button>
            </div>
            <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "6px", textAlign: "center" }}>Enter to send · 👍👎 teaches the AI · 📌 saves to notes</p>
          </div>
        </main>

        {/* Notes Panel */}
        {showNotes && (
          <aside style={{ width: "300px", borderLeft: "1px solid var(--border)", background: "var(--bg-card)", display: "flex", flexDirection: "column" }}>
            <div style={{ padding: "16px", borderBottom: "1px solid var(--border)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <h3 style={{ fontSize: "15px" }}>📌 Notes ({notes.length})</h3>
              <div style={{ display: "flex", gap: "6px" }}>
                <button onClick={downloadNotesPDF} title="Download notes" style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "4px 8px", fontSize: "12px", cursor: "pointer" }}>⬇ Download</button>
                <button onClick={() => setEmailModal(true)} title="Email notes" style={{ background: "var(--bg-secondary)", border: "1px solid var(--border)", borderRadius: "8px", padding: "4px 8px", fontSize: "12px", cursor: "pointer" }}>📧 Email</button>
                <button onClick={() => setShowNotes(false)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: "16px" }}>✕</button>
              </div>
            </div>
            <div style={{ flex: 1, overflowY: "auto", padding: "12px" }}>
              {notes.length === 0 ? (
                <div style={{ textAlign: "center", padding: "32px 16px" }}>
                  <div style={{ fontSize: "32px", marginBottom: "12px" }}>📌</div>
                  <p style={{ fontSize: "13px", color: "var(--text-muted)" }}>No notes yet.</p>
                  <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "6px" }}>Click 📌 Save on any AI response to save it here.</p>
                </div>
              ) : (
                notes.map((note) => (
                  <div key={note.id} style={{ padding: "12px", borderRadius: "var(--radius-sm)", background: "var(--bg-secondary)", border: "1px solid var(--border)", marginBottom: "8px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "6px" }}>
                      <div>
                        <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--text-secondary)" }}>{note.docName}</span>
                        <p style={{ fontSize: "10px", color: "var(--text-muted)" }}>{note.savedAt}</p>
                      </div>
                      <button onClick={() => deleteNote(note.id)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)", fontSize: "14px" }}>✕</button>
                    </div>
                    <p style={{ fontSize: "13px", lineHeight: "1.6", color: "var(--text-primary)" }}>{note.content.substring(0, 200)}{note.content.length > 200 ? "..." : ""}</p>
                  </div>
                ))
              )}
            </div>
          </aside>
        )}
      </div>
      {showQuiz && selectedDoc && (
        <QuizPanel
          documentId={selectedDoc.id}
          workspaceId={WORKSPACE_ID}
          documentName={selectedDoc.name}
          onClose={() => setShowQuiz(false)}
        />
      )}
    </div>
  );
}
