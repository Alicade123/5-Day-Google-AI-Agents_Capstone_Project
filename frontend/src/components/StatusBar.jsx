export default function StatusBar({ health, metrics }) {
  return (
    <div className="status-bar">
      <span className={`status ${health?.status || "unknown"}`}>
        API: {health?.status || "unknown"}
      </span>
      {health?.services &&
        Object.entries(health.services).map(([name, status]) => (
          <span key={name} className={`status ${status}`}>
            {name}: {status}
          </span>
        ))}
      <span className="muted">
        Last collected: {metrics?.collected_at ? new Date(metrics.collected_at).toLocaleTimeString() : "—"}
      </span>
    </div>
  );
}
