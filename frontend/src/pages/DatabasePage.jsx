import { useState, useEffect, useCallback } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const PAGE_SIZE = 50;

export default function DatabasePage() {
  const [attacks, setAttacks] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [dataSource, setDataSource] = useState("");
  const [province, setProvince] = useState("");
  const [year, setYear] = useState("");
  const [perpetrator, setPerpetrator] = useState("");
  const [search, setSearch] = useState("");
  const [searchDebounced, setSearchDebounced] = useState("");
  const [provinces, setProvinces] = useState([]);
  const [perpetrators, setPerpetrators] = useState([]);
  const [years, setYears] = useState([]);

  useEffect(() => {
    const t = setTimeout(() => setSearchDebounced(search), 350);
    return () => clearTimeout(t);
  }, [search]);

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
        const y = Object.keys(d.by_year || {}).sort((a, b) => Number(b) - Number(a));
        setYears(y);
      })
      .catch(() => {});
  }, []);

  const fetchAttacks = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (province) params.append("province", province);
      if (year) params.append("year", year);
      if (perpetrator) params.append("perpetrator", perpetrator);
      if (searchDebounced) params.append("q", searchDebounced);
      params.append("limit", String(PAGE_SIZE));
      params.append("offset", String(page * PAGE_SIZE));

      const res = await fetch(`${API_BASE}/attacks/?${params}`);
      const data = await res.json();
      setAttacks(data.data || []);
      setTotal(data.total || 0);
      setHasMore(Boolean(data.has_more));
      setDataSource(data.data_source || "");
    } catch {
      setAttacks([]);
      setTotal(0);
      setHasMore(false);
    }
    setLoading(false);
  }, [province, year, perpetrator, searchDebounced, page]);

  useEffect(() => {
    fetchAttacks();
  }, [fetchAttacks]);

  useEffect(() => {
    setPage(0);
  }, [province, year, perpetrator, searchDebounced]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pageStart = total === 0 ? 0 : page * PAGE_SIZE + 1;
  const pageEnd = Math.min((page + 1) * PAGE_SIZE, total);

  return (
    <div className="db-page">
      <div className="page-header">
        <div className="page-header-inner">
          <div>
            <div className="page-eyebrow">Knowledge Base</div>
            <div className="page-title">Attack Database</div>
            <div className="page-meta">
              {total > 0
                ? `${total.toLocaleString()} incidents${dataSource ? ` · ${dataSource}` : ""}`
                : "Browse and filter documented incidents"}
            </div>
          </div>
        </div>
      </div>

      {dataSource === "fallback" && (
        <div className="data-warning">
          Only a small sample dataset is loaded. Configure Supabase in <code>backend/.env</code> or mount CSV files to show all 1,704 incidents.
        </div>
      )}

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
            setPage(0);
          }}
        >
          Reset
        </button>

        <div className="result-count">
          {total.toLocaleString()} records
        </div>
      </div>

      <div className="attacks-table-wrap">
        {loading ? (
          <div className="loading">
            <div className="loading-spinner" />
            Loading attack records…
          </div>
        ) : attacks.length === 0 ? (
          <div className="empty-state">
            <div className="empty-title">No records found</div>
            <p>Try clearing filters or searching a different city, year, or group.</p>
          </div>
        ) : (
          <>
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
                {attacks.map((a) => (
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

            <div className="pagination-bar">
              <span className="pagination-info">
                Showing {pageStart.toLocaleString()}–{pageEnd.toLocaleString()} of {total.toLocaleString()}
              </span>
              <div className="pagination-controls">
                <button
                  type="button"
                  className="btn-ghost"
                  disabled={page === 0 || loading}
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                >
                  Previous
                </button>
                <span className="pagination-page">
                  Page {page + 1} of {totalPages.toLocaleString()}
                </span>
                <button
                  type="button"
                  className="btn-ghost"
                  disabled={!hasMore || loading}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
