import { useState, useRef, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const SUGGESTIONS = [
  "What was the deadliest attack in Pakistan?",
  "Tell me about the Peshawar school attack 2014",
  "Which group has carried out the most attacks?",
  "How many people were killed in Karachi blasts?",
  "What attacks happened in Balochistan?",
  "Tell me about TTP attacks since 2020",
];

function formatMessage(text) {
  // Bold **text**
  return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
}

function MessageBubble({ msg }) {
  const isBot = msg.role === "assistant";
  const timeStr = msg.time ? new Date(msg.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : "";

  return (
    <div className={`message ${isBot ? "bot" : "user"}`}>
      <div className={`msg-avatar ${isBot ? "bot" : "user-av"}`}>
        {isBot ? "🔍" : "👤"}
      </div>
      <div className="msg-body">
        <div
          className="msg-bubble"
          dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
        />
        {isBot && msg.sources && msg.sources.length > 0 && (
          <div className="msg-sources">
            {msg.sources.map((s, i) => (
              <span key={i} className="source-tag">
                {s.date} · {s.deaths}☩ · {s.source}
              </span>
            ))}
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
      <div className="msg-avatar bot">🔍</div>
      <div className="msg-body">
        <div className="typing-indicator">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const bottomRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function sendMessage(text) {
    const msg = text || input.trim();
    if (!msg || loading) return;

    setInput("");
    setMessages(prev => [...prev, {
      role: "user", content: msg, time: new Date().toISOString()
    }]);
    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, session_id: sessionId, history: [] })
      });

      const data = await res.json();
      setSessionId(data.session_id);
      setMessages(prev => [...prev, {
        role: "assistant",
        content: data.response,
        sources: data.sources,
        time: new Date().toISOString()
      }]);
    } catch (e) {
      setMessages(prev => [...prev, {
        role: "assistant",
        content: "⚠️ Could not connect to the backend. Please check if the backend service is running and accessible.",
        time: new Date().toISOString()
      }]);
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
      {/* Header */}
      <div className="page-header">
        <div className="page-header-inner">
          <div>
            <div className="page-eyebrow">Intelligence Chatbot</div>
            <div className="page-title">Ask the Database</div>
          </div>
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              style={{
                background: "none", border: "1px solid var(--border)", color: "var(--text3)",
                padding: "6px 14px", borderRadius: "6px", cursor: "pointer",
                fontSize: "12px", fontFamily: "'JetBrains Mono', monospace"
              }}
            >
              Clear Chat
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <span className="welcome-icon">🇵🇰</span>
            <div className="welcome-title">Pakistan Terror Intelligence</div>
            <p className="welcome-sub">
              Ask me about any terror attack in Pakistan — dates, locations, casualty counts,
              perpetrator groups, and more. Powered by a structured knowledge base + Grok 4.1.
            </p>
            <div className="suggestion-chips">
              {SUGGESTIONS.map((s, i) => (
                <button key={i} className="chip" onClick={() => sendMessage(s)}>{s}</button>
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

      {/* Input */}
      <div className="chat-input-area">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            className="chat-textarea"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about any Pakistan terror attack..."
            rows={1}
          />
          <button
            className="send-btn"
            onClick={() => sendMessage()}
            disabled={loading || !input.trim()}
          >
            ➤
          </button>
        </div>
        <div className="input-hint">ENTER to send · SHIFT+ENTER for new line</div>
      </div>
    </div>
  );
}
