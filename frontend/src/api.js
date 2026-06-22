const API_BASE = import.meta.env.VITE_API_URL || "/api";

export async function fetchJSON(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${path}`);
  }
  return response.json();
}

export const api = {
  health: () => fetchJSON("/health"),
  metrics: () => fetchJSON("/metrics"),
  trends: (minutes = 15) => fetchJSON(`/history/trends?window_minutes=${minutes}`),
  incidents: () => fetchJSON("/incidents"),
  correlation: () => fetchJSON("/correlation?window_hours=1"),
  query: (query) =>
    fetchJSON("/agent/query", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),
  analyze: () => fetchJSON("/analyze", { method: "POST" }),
};
