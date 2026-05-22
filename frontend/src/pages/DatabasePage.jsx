import { useState, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export default function DatabasePage() {
  const [attacks, setAttacks] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [province, setProvince] = useState("");
  const [year, setYear] = useState("");
  const [perpetrator, setPerpetrator] = useState("");
  const [provinces, setProvinces] = useState([]);
  const [perpetrators, setPerpetrators] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/attacks/provinces`).then(r => r.json()).then(d => setProvinces(d.provinces || [])).catch(() => {});
    fetch(`${API_BASE}/attacks/perpetrators`).then(r => r.json()).then(d => setPerpetrators(d.perpetrators || [])).catch(() => {});
  }, []);

  useEffect(() => {
    fetchAttacks();
  }, [province, year, perpetrator]);

  async function fetchAttacks() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (province) params.append("province", province);
      if (year) params.append("year", year);
      if (perpetrator) params.append("perpetrator", perpetrator);
      params.append("limit", "50");

      const res = await fetch(`${API_BASE}/attacks/?${params}`);
      const data = await res.json();
      setAttacks(data.data || []);
      setTotal(data.total || 0);
    } catch (e) {
      setAttacks([]);
    }
    setLoading(false);
  }

  const YEARS = ["2007","2008","2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021","2022","2023","2024","2025"];

  return (
    <div className="db-page">
      <div className="page-header">
        <div className="page-header-inner">
          <div>
            <div className="page-eyebrow">Knowledge Base</div>
            <div className="page-title">Attack Database</div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="filters-bar">
        <span className="filter-label">FILTER:</span>

        <select className="filter-select" value={province} onChange={e => setProvince(e.target.value)}>
          <option value="">All Provinces</option>
          {provinces.map(p => <option key={p} value={p}>{p}</option>)}
        </select>

        <select className="filter-select" value={year} onChange={e => setYear(e.target.value)}>
          <option value="">All Years</option>
          {YEARS.map(y => <option key={y} value={y}>{y}</option>)}
        </select>

        <select className="filter-select" value={perpetrator} onChange={e => setPerpetrator(e.target.value)}>
          <option value="">All Groups</option>
          {perpetrators.map(p => <option key={p} value={p}>{p}</option>)}
        </select>

        <button
          onClick={() => { setProvince(""); setYear(""); setPerpetrator(""); }}
          style={{
            background: "none", border: "1px solid var(--border)", color: "var(--text3)",
            padding: "6px 12px", borderRadius: "6px", cursor: "pointer",
            fontSize: "12px", fontFamily: "'JetBrains Mono', monospace"
          }}
        >
          Reset
        </button>

        <div className="result-count">{total} records</div>
      </div>

      {/* Table */}
      <div className="attacks-table-wrap">
        {loading ? (
          <div className="loading">Loading attack records...</div>
        ) : (
          <table className="attacks-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Location</th>
                <th>Attack Type</th>
                <th>Perpetrator</th>
                <th>Deaths</th>
                <th>Injuries</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {attacks.map(a => (
                <tr key={a.id}>
                  <td className="date-cell">{a.date}</td>
                  <td>
                    <div className="location-main">{a.location.split(',')[0]}</div>
                    <div className="location-prov">{a.province}</div>
                  </td>
                  <td style={{ fontSize: 12, color: "var(--text2)" }}>{a.attack_type}</td>
                  <td><span className="group-tag">{a.perpetrator.split(' ').slice(0,2).join(' ')}</span></td>
                  <td><span className="death-count">{a.deaths}</span></td>
                  <td style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12, color: "var(--text2)" }}>{a.injuries}</td>
                  <td className="desc-cell">{a.description.slice(0, 120)}...</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {!loading && attacks.length === 0 && (
          <div className="loading">No records match your filters.</div>
        )}
      </div>
    </div>
  );
}
