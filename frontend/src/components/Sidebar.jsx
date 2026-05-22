import { useEffect, useState } from "react";
import { API_BASE } from "../config/api";

export default function Sidebar({ currentPage, onNavigate, isOpen, onToggle }) {
  const [apiStatus, setApiStatus] = useState("checking");
  const [recordCount, setRecordCount] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/health`)
      .then(r => r.json())
      .then(d => {
        setApiStatus(d.mode || "demo");
        setRecordCount(d.total_incidents);
      })
      .catch(() => setApiStatus("offline"));
  }, []);

  const navItems = [
    { id: "chat", icon: "◆", label: "Intelligence Chat" },
    { id: "database", icon: "▤", label: "Attack Database" },
    { id: "stats", icon: "▥", label: "Statistics" },
  ];

  return (
    <>
      <button className="sidebar-toggle" onClick={onToggle} title="Toggle sidebar">
        {isOpen ? "✕" : "☰"}
      </button>

      <aside className={`sidebar ${isOpen ? "" : "closed"}`}>
        <div className="sidebar-brand">
          <div className="brand-flag">
            <div className="flag-strip" />
            <div>
              <div className="brand-title">Pakistan Terror Attacks</div>
              <div className="brand-title">Intelligence System</div>
            </div>
          </div>
          <div className="brand-sub">AI-Powered Research Tool</div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-label">Navigation</div>
          {navItems.map(item => (
            <button
              key={item.id}
              className={`nav-item ${currentPage === item.id ? "active" : ""}`}
              onClick={() => onNavigate(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="api-status">
            <div className={`status-dot ${apiStatus === "live" ? "live" : ""}`} />
            {apiStatus === "live" ? "AI agent · search + Grok" :
             apiStatus === "demo" ? "Search agent (add GROK_API_KEY)" : "Backend Offline"}
          </div>
          {recordCount != null && (
            <div className="sidebar-records">{recordCount.toLocaleString()} records loaded</div>
          )}
        </div>
      </aside>
    </>
  );
}
