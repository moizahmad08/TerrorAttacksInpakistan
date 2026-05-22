import { useState, useRef, useEffect } from "react";
import { FormattedMessage } from "../utils/formatMessage";
import { API_BASE } from "../config/api";

const SUGGESTIONS = [
  "What was the deadliest attack in Pakistan?",
  "Tell me about the Peshawar school attack in 2014",
  "How many total incidents are in the database?",
  "What attacks happened in Balochistan?",
  "List TTP attacks since 2020",
  "Show statistics by province",
];

const INTENT_LABELS = {
  statistics: "Statistics",
  temporal: "Timeline",
  location: "Location",
  perpetrator: "Group",
  ranking: "Ranking",
  incident: "Incident lookup",
  general: "Research",
};

const MODE_LABELS = {
  ai: "Grok AI · Answered from search",
  database: "Database search · Summary",
};

function SourceCard({ source }) {
  return (
    <div className="source-card">
      <div className="source-card-top">
        <span className="source-date">{source.date}</span>
        <span className="source-deaths">{source.deaths} killed</span>
      </div>
      <div className="source-location">{source.location}</div>
      {source.province && <div className="source-meta">{source.province}</div>}
      <div className="source-meta">
        {source.attack_type && <span>{source.attack_type}</span>}
        {source.perpetrator && <span> · {source.perpetrator}</span>}
      </div>
    </div>
  );
}

function MessageBubble({ msg }) {
  const isBot = msg.role === "assistant";
  const timeStr = msg.time
    ? new Date(msg.time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "";

  return (
    <div className={`message ${isBot ? "bot" : "user"}`}>
      <div className={`msg-avatar ${isBot ? "bot" : "user-av"}`}>
        {isBot ? "PA" : "You"}
      </div>
      <div className="msg-body">
        {isBot && (
          <div className="msg-badges">
            {msg.mode && (
              <span className={`mode-badge ${msg.mode === "ai" ? "mode-ai" : ""}`}>
                {MODE_LABELS[msg.mode] || msg.mode}
              </span>
            )}
            {msg.intent && (
              <span className="intent-badge">{INTENT_LABELS[msg.intent] || msg.intent}</span>
            )}
          </div>
        )}
        <div className="msg-bubble">
          {isBot ? (
            <FormattedMessage content={msg.content} />
          ) : (
            <p className="msg-p user-text">{msg.content}</p>
          )}
        </div>
        {isBot && msg.sources && msg.sources.length > 0 && (
          <div className="msg-sources-block">
            <div className="msg-sources-label">Referenced records</div>
            <div className="msg-sources-grid">
              {msg.sources.map((s, i) => (
                <SourceCard key={s.id || i} source={s} />
              ))}
            </div>
          </div>
        )}
        {timeStr && <div className="msg-time">{timeStr}</div>}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="message bot">
      <div className="msg-avatar bot">PA</div>
      <div className="msg-body">
        <div className="typing-indicator">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
        <span className="typing-label">Searching database and preparing answer…</span>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [recordCount, setRecordCount] = useState(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    fetch(`${API_BASE}/attacks/stats`)
      .then((r) => r.json())
      .then((d) => setRecordCount(d.total_incidents))
      .catch(() => {});
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [input]);

  async function sendMessage(text) {
    const msg = text || input.trim();
    if (!msg || loading) return;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: msg, time: new Date().toISOString() },
    ]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, session_id: sessionId, history: [] }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Request failed");
      }

      const data = await res.json();
      setSessionId(data.session_id);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          sources: data.sources,
          intent: data.intent,
          mode: data.mode,
          time: new Date().toISOString(),
        },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            `## Connection error\n\nCould not reach the API at \`${API_BASE}\`.\n\n- **Docker:** \`docker compose up -d --build\` then open **http://localhost:8095**\n- **Local dev:** backend \`uvicorn main:app --port 8000\` and \`npm run dev\` (port 3000)\n- Check: \`curl http://localhost:8095/api/health\``,
          time: new Date().toISOString(),
        },
      ]);
    }
    setLoading(false);
    textareaRef.current?.focus();
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  async function clearChat() {
    if (sessionId) {
      try {
        await fetch(`${API_BASE}/chat/session/${sessionId}`, { method: "DELETE" });
      } catch {}
    }
    setMessages([]);
    setSessionId(null);
  }

  return (
    <div className="chat-layout">
      <div className="page-header">
        <div className="page-header-inner">
          <div>
            <div className="page-eyebrow">Intelligence Chatbot</div>
            <div className="page-title">Ask the Database</div>
            {recordCount != null && (
              <div className="page-meta">{recordCount.toLocaleString()} incidents indexed</div>
            )}
          </div>
          {messages.length > 0 && (
            <button type="button" className="btn-ghost" onClick={clearChat}>
              Clear chat
            </button>
          )}
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <div className="welcome-badge">Knowledge base · 1947–2026</div>
            <div className="welcome-title">Pakistan Terror Intelligence</div>
            <p className="welcome-sub">
              Ask any question about Pakistan terror attacks. The agent searches the database first,
              then answers in natural language with sources cited below.
            </p>
            <div className="suggestion-chips">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} type="button" className="chip" onClick={() => sendMessage(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}

        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about any Pakistan terror attack…"
            rows={1}
            disabled={loading}
          />
          <button
            type="button"
            className="send-btn"
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
            aria-label="Send message"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
            </svg>
          </button>
        </div>
        <div className="input-hint">Enter to send · Shift+Enter for new line</div>
      </div>
    </div>
  );
}
