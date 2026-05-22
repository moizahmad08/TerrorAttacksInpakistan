import { useState, useEffect, useMemo } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export default function DatabasePage() {
  const [attacks, setAttacks] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [province, setProvince] = useState("");
  const [year, setYear] = useState("");
  const [perpetrator, setPerpetrator] = useState("");
  const [search, setSearch] = useState("");
  const [provinces, setProvinces] = useState([]);
  const [perpetrators, setPerpetrators] = useState([]);
  const [years, setYears] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/attacks/provinces`)
      .then((r) => r.json())
      .then((d) => setProvinces(d.provinces || []))
      .catch(() => {});
    fetch(`${API_BASE}/attacks/perpetrators`)
      .then((r) => r.json())
      .then((d) => setPerpetrators(d.perpetrators || []))
      .catch(() => {});
    fetch(`${API_BASE}/attacks/stats`)
      .then((r) => r.json())
      .then((d) => {
        const y = Object.keys(d.by_year || {})
          .sort((a, b) => Number(b) - Number(a));
        setYears(y);
      })
      .catch(() => {});
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
      params.append("limit", "100");

      const res = await fetch(`${API_BASE}/attacks/?${params}`);
      const data = await res.json();
      setAttacks(data.data || []);
      setTotal(data.total || 0);
    } catch {
      setAttacks([]);
      setTotal(0);
    }
    setLoading(false);
  }

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return attacks;
    return attacks.filter(
      (a) =>
        a.location?.toLowerCase().includes(q) ||
        a.province?.toLowerCase().includes(q) ||
        a.perpetrator?.toLowerCase().includes(q) ||
        a.attack_type?.toLowerCase().includes(q) ||
        a.description?.toLowerCase().includes(q) ||
        a.date?.includes(q)
    );
  }, [attacks, search]);

  return (
    <div className="db-page">
      <div className="page-header">
        <div className="page-header-inner">
          <div>
            <div className="page-eyebrow">Knowledge Base</div>
            <div className="page-title">Attack Database</div>
            <div className="page-meta">Browse and filter documented incidents</div>
          </div>
        </div>
      </div>

      <div className="filters-bar">
        <input
          type="search"
          className="filter-search"
          placeholder="Search location, group, type…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />

        <select className="filter-select" value={province} onChange={(e) => setProvince(e.target.value)}>
          <option value="">All provinces</option>
          {provinces.map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        <select className="filter-select" value={year} onChange={(e) => setYear(e.target.value)}>
          <option value="">All years</option>
          {years.map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>

        <select className="filter-select" value={perpetrator} onChange={(e) => setPerpetrator(e.target.value)}>
          <option value="">All groups</option>
          {perpetrators.map((p) => (
            <option key={p} value={p}>{p.length > 40 ? p.slice(0, 40) + "…" : p}</option>
          ))}
        </select>

        <button
          type="button"
          className="btn-ghost"
          onClick={() => {
            setProvince("");
            setYear("");
            setPerpetrator("");
            setSearch("");
          }}
        >
          Reset
        </button>

        <div className="result-count">
          {search ? `${filtered.length} shown` : `${total.toLocaleString()} records`}
        </div>
      </div>

      <div className="attacks-table-wrap">
        {loading ? (
          <div className="loading">
            <div className="loading-spinner" />
            Loading attack records…
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-title">No records found</div>
            <p>Try clearing filters or searching a different city, year, or group.</p>
          </div>
        ) : (
          <table className="attacks-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Location</th>
                <th>Type</th>
                <th>Perpetrator</th>
                <th>Killed</th>
                <th>Injured</th>
                <th>Summary</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={a.id}>
                  <td className="date-cell">{a.date}</td>
                  <td>
                    <div className="location-main">{a.location?.split(",")[0] || a.location}</div>
                    <div className="location-prov">{a.province}</div>
                  </td>
                  <td className="type-cell">{a.attack_type}</td>
                  <td>
                    <span className="group-tag" title={a.perpetrator}>
                      {a.perpetrator?.length > 28 ? a.perpetrator.slice(0, 28) + "…" : a.perpetrator}
                    </span>
                  </td>
                  <td><span className="death-count">{a.deaths}</span></td>
                  <td className="injury-cell">{a.injuries}</td>
                  <td className="desc-cell" title={a.description}>
                    {(a.description || "").length > 140
                      ? a.description.slice(0, 140) + "…"
                      : a.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
