"use client";

import { useState } from "react";

interface QuizOption {
  label: string;
  text: string;
  is_correct: boolean;
}

interface QuizQuestion {
  question: string;
  options: QuizOption[];
  explanation: string;
}

interface QuizProps {
  documentId: string;
  workspaceId: string;
  documentName: string;
  onClose: () => void;
}

export default function QuizPanel({ documentId, workspaceId, documentName, onClose }: QuizProps) {
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [score, setScore] = useState(0);

  async function generateQuiz() {
    setLoading(true);
    setAnswers({});
    setSubmitted(false);
    try {
      const res = await fetch("http://localhost:8000/api/v1/quiz/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          workspace_id: workspaceId,
          document_id: documentId,
          num_questions: 5,
          quiz_type: "mcq",
        }),
      });
      const data = await res.json();
      setQuestions(data.questions || []);
    } catch (e) {
      alert("Failed to generate quiz.");
    } finally {
      setLoading(false);
    }
  }

  function handleAnswer(qIndex: number, label: string) {
    if (submitted) return;
    setAnswers((prev) => ({ ...prev, [qIndex]: label }));
  }

  function handleSubmit() {
    let correct = 0;
    questions.forEach((q, i) => {
      const selected = answers[i];
      const correctOption = q.options.find((o) => o.is_correct);
      if (selected === correctOption?.label) correct++;
    });
    setScore(correct);
    setSubmitted(true);
  }

  function getOptionStyle(q: QuizQuestion, option: QuizOption, qIndex: number) {
    const selected = answers[qIndex];
    const base: any = {
      padding: "10px 14px", borderRadius: "var(--radius-sm)",
      border: "1px solid var(--border)", cursor: submitted ? "default" : "pointer",
      fontSize: "13px", marginBottom: "6px", transition: "all 0.15s",
      display: "flex", alignItems: "center", gap: "10px",
      background: "var(--bg-primary)",
    };
    if (!submitted) {
      if (selected === option.label) return { ...base, background: "var(--accent-lavender)", borderColor: "var(--border-hover)" };
      return base;
    }
    if (option.is_correct) return { ...base, background: "var(--accent-sage)", borderColor: "var(--accent-sage)" };
    if (selected === option.label && !option.is_correct) return { ...base, background: "var(--accent-rose)", borderColor: "var(--accent-rose)" };
    return { ...base, opacity: 0.6 };
  }

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(44,36,32,0.5)", zIndex: 1000, display: "flex", alignItems: "center", justifyContent: "center", padding: "24px" }}>
      <div style={{ background: "var(--bg-card)", border: "1px solid var(--border)", borderRadius: "var(--radius-lg)", width: "100%", maxWidth: "680px", maxHeight: "85vh", display: "flex", flexDirection: "column", boxShadow: "var(--shadow-strong)" }}>
        <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h2 style={{ fontSize: "18px" }}>🧪 Quiz</h2>
            <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>{documentName}</p>
          </div>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "20px", color: "var(--text-muted)" }}>✕</button>
        </div>
        <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
          {questions.length === 0 ? (
            <div style={{ textAlign: "center", padding: "40px 20px" }}>
              <div style={{ fontSize: "48px", marginBottom: "16px" }}>🧪</div>
              <h3 style={{ fontSize: "18px", marginBottom: "8px" }}>Test your knowledge</h3>
              <p style={{ fontSize: "14px", color: "var(--text-muted)", marginBottom: "24px" }}>Generate 5 MCQ questions from this document using AI.</p>
              <button onClick={generateQuiz} disabled={loading} className="btn-primary" style={{ padding: "12px 32px", fontSize: "14px" }}>
                {loading ? "Generating..." : "✦ Generate Quiz"}
              </button>
            </div>
          ) : (
            <>
              {submitted && (
                <div style={{ padding: "16px", borderRadius: "var(--radius)", background: score >= 4 ? "var(--accent-sage)" : score >= 3 ? "var(--accent-peach)" : "var(--accent-rose)", marginBottom: "24px", textAlign: "center" }}>
                  <p style={{ fontSize: "20px", fontWeight: 600 }}>Score: {score}/{questions.length}</p>
                  <p style={{ fontSize: "14px", marginTop: "4px" }}>
                    {score === questions.length ? "Perfect! 🎉" : score >= 4 ? "Great job! 👏" : score >= 3 ? "Good effort! 💪" : "Keep studying! 📚"}
                  </p>
                </div>
              )}
              {questions.map((q, qIndex) => (
                <div key={qIndex} style={{ marginBottom: "28px" }}>
                  <p style={{ fontSize: "14px", fontWeight: 600, marginBottom: "12px", lineHeight: "1.5" }}>
                    <span style={{ color: "var(--text-muted)", marginRight: "8px" }}>Q{qIndex + 1}.</span>
                    {q.question}
                  </p>
                  {q.options.map((option) => (
                    <div key={option.label} onClick={() => handleAnswer(qIndex, option.label)} style={getOptionStyle(q, option, qIndex)}>
                      <span style={{ width: "24px", height: "24px", borderRadius: "50%", background: "var(--bg-secondary)", border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "12px", fontWeight: 600, flexShrink: 0 }}>
                        {option.label}
                      </span>
                      {option.text}
                    </div>
                  ))}
                  {submitted && (
                    <p style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "8px", padding: "8px 12px", background: "var(--bg-secondary)", borderRadius: "var(--radius-sm)" }}>
                      💡 {q.explanation}
                    </p>
                  )}
                </div>
              ))}
            </>
          )}
        </div>
        {questions.length > 0 && (
          <div style={{ padding: "16px 24px", borderTop: "1px solid var(--border)", display: "flex", gap: "10px", justifyContent: "flex-end" }}>
            <button onClick={generateQuiz} disabled={loading} className="btn-ghost">{loading ? "Generating..." : "↻ New Quiz"}</button>
            {!submitted && Object.keys(answers).length === questions.length && (
              <button onClick={handleSubmit} className="btn-primary">Submit Answers ✦</button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
