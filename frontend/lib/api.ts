const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadDocument(file: File, workspaceId: string, uploadedBy: string) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(API_URL + "/api/v1/documents/upload?workspace_id=" + workspaceId + "&uploaded_by=" + uploadedBy, { method: "POST", body: formData });
  if (!res.ok) throw new Error("Upload failed");
  return res.json();
}

export async function listDocuments(workspaceId: string) {
  const res = await fetch(API_URL + "/api/v1/documents/workspace/" + workspaceId);
  if (!res.ok) throw new Error("Failed to fetch documents");
  return res.json();
}

export async function askQuestion(question: string, workspaceId: string, documentId?: string) {
  const res = await fetch(API_URL + "/api/v1/chat/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, workspace_id: workspaceId, document_id: documentId || null, top_k: 5 }),
  });
  if (!res.ok) throw new Error("Chat failed");
  return res.json();
}

export async function submitFeedback(
  feedbackType: "thumbs_up" | "thumbs_down",
  question: string,
  answer: string,
  workspaceId: string,
  chunkIds: string[],
  documentId?: string,
) {
  const res = await fetch(API_URL + "/api/v1/feedback/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ feedback_type: feedbackType, question, answer, workspace_id: workspaceId, chunk_ids: chunkIds, document_id: documentId || null }),
  });
  if (!res.ok) throw new Error("Feedback failed");
  return res.json();
}

export async function sendNotesEmail(toEmail: string, notes: object[]) {
  const res = await fetch(API_URL + "/api/v1/email/send-notes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ to_email: toEmail, notes }),
  });
  if (!res.ok) throw new Error("Email failed");
  return res.json();
}
