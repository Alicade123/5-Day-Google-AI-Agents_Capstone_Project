export default function TrendChart({ trends }) {
  const averages = trends?.moving_averages || {};
  const entries = Object.entries(averages);

  return (
    <div className="panel">
      <h2>Trend Averages ({trends?.window_minutes || 15} min)</h2>
      {entries.length === 0 && <p className="muted">Collecting trend data...</p>}
      <div className="chart-bars">
        {entries.map(([key, value]) => (
          <div key={key} className="bar-row">
            <label>{key.replace("_", " ")}</label>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${Math.min(value, 100)}%` }} />
            </div>
            <span>{value}%</span>
          </div>
        ))}
      </div>
      <p className="muted">{trends?.observations || 0} observations</p>
    </div>
  );
}
