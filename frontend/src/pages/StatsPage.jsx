import { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function BarChart({ data, color = "var(--red)", maxVal }) {
  const max = maxVal || Math.max(...Object.values(data));
  return (
    <div className="bar-chart">
      {Object.entries(data)
        .sort((a, b) => b[1] - a[1])
        .map(([label, val]) => (
          <div key={label} className="bar-row">
            <div className="bar-label" title={label}>{label}</div>
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{ width: `${(val / max) * 100}%`, background: color }}
              />
            </div>
            <div className="bar-value">{val}</div>
          </div>
        ))}
    </div>
  );
}

export default function StatsPage() {
  const [stats, setStats] = useState(null);
  const [deadliest, setDeadliest] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API_BASE}/attacks/stats`).then(r => r.json()),
      fetch(`${API_BASE}/attacks/deadliest?limit=5`).then(r => r.json())
    ]).then(([s, d]) => {
      setStats(s);
      setDeadliest(d.data || []);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner" />
        Loading statistics…
      </div>
    );
  }
  if (!stats) {
    return (
      <div className="empty-state">
        <div className="empty-title">Could not load statistics</div>
        <p>Ensure the backend is running (Docker: port 8095 with API proxy, or local dev: port 8000).</p>
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-header-inner">
          <div>
            <div className="page-eyebrow">Analysis</div>
            <div className="page-title">Statistics Overview</div>
            <div className="page-meta">Aggregated from full knowledge base</div>
          </div>
        </div>
      </div>

      <div className="stats-page">
        {/* Top KPIs */}
        <div className="stat-grid">
          <div className="stat-card red">
            <div className="stat-num">{stats.total_incidents}</div>
            <div className="stat-label">Total Incidents</div>
          </div>
          <div className="stat-card amber">
            <div className="stat-num">{stats.total_deaths.toLocaleString()}</div>
            <div className="stat-label">Total Deaths</div>
          </div>
          <div className="stat-card teal">
            <div className="stat-num">{stats.total_injuries.toLocaleString()}</div>
            <div className="stat-label">Total Injuries</div>
          </div>
          <div className="stat-card purple">
            <div className="stat-num">
              {Math.round(stats.total_deaths / stats.total_incidents)}
            </div>
            <div className="stat-label">Avg Deaths / Attack</div>
          </div>
        </div>

        {/* Deadliest Attacks */}
        <div>
          <div className="section-title">5 Deadliest Attacks</div>
          <table className="attacks-table">
            <thead>
              <tr>
                <th>Rank</th>
                <th>Date</th>
                <th>Location</th>
                <th>Deaths</th>
                <th>Perpetrator</th>
              </tr>
            </thead>
            <tbody>
              {deadliest.map((a, i) => (
                <tr key={a.id}>
                  <td style={{ fontFamily: "'JetBrains Mono', monospace", color: "var(--text3)" }}>#{i + 1}</td>
                  <td className="date-cell">{a.date}</td>
                  <td>
                    <div className="location-main">{a.location.split(',')[0]}</div>
                    <div className="location-prov">{a.province}</div>
                  </td>
                  <td><span className="death-count">{a.deaths}</span></td>
                  <td><span className="group-tag">{a.perpetrator.split(' ').slice(0,3).join(' ')}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Charts */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "28px" }}>
          <div>
            <div className="section-title">Attacks by Province</div>
            <BarChart data={stats.by_province} color="var(--red)" />
          </div>
          <div>
            <div className="section-title">Attacks by Year</div>
            <BarChart data={stats.by_year} color="var(--amber)" />
          </div>
          <div>
            <div className="section-title">By Perpetrator Group</div>
            <BarChart
              data={Object.fromEntries(
                Object.entries(stats.by_perpetrator).map(([k, v]) => [k.split('(')[0].trim(), v])
              )}
              color="var(--teal)"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
