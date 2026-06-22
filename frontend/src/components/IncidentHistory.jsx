export default function IncidentHistory({ incidents }) {
  return (
    <div className="panel">
      <h2>Incident History</h2>
      {incidents?.length === 0 && <p className="muted">No incidents recorded</p>}
      <ul className="incidents">
        {incidents?.map((inc) => (
          <li key={inc.id}>
            <div className="incident-header">
              <strong>{inc.title}</strong>
              <span className={`badge ${inc.severity}`}>{inc.severity}</span>
            </div>
            <p className="muted">{inc.summary}</p>
            <small>{new Date(inc.created_at).toLocaleString()}</small>
          </li>
        ))}
      </ul>
    </div>
  );
}
