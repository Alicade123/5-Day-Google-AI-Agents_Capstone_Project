export default function MetricCard({ title, value, unit }) {
  const display = value != null ? `${value}${unit === "%" ? "" : " "}${unit}` : "—";
  const level =
    title === "CPU" && value >= 90
      ? "critical"
      : title === "Memory" && value >= 85
        ? "warning"
        : "ok";

  return (
    <div className={`metric-card ${level}`}>
      <h3>{title}</h3>
      <p className="value">{display}</p>
    </div>
  );
}
