/**
 * API base URL.
 * - Production/Docker (8095): use /api (nginx proxies to backend:8000)
 * - Local dev: set VITE_API_URL=http://localhost:8000/api or use /api + vite proxy
 */
export const API_BASE =
  import.meta.env.VITE_API_URL?.trim() ||
  (import.meta.env.DEV ? "http://localhost:8000/api" : "/api");
