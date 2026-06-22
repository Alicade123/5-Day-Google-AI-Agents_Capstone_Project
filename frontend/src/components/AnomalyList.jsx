export default function AnomalyList({ anomalies, summaries }) {
  return (
    <div className="panel">
      <h2>Anomalies & Trends</h2>
      {summaries?.length > 0 && (
        <ul className="summaries">
          {summaries.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      )}
      {anomalies?.length === 0 && <p className="muted">No active anomalies</p>}
      <ul>
        {anomalies?.map((a, i) => (
          <li key={i} className={`severity-${a.severity}`}>
            <strong>{a.metric}</strong>: {a.description}
          </li>
        ))}
      </ul>
    </div>
  );
}
