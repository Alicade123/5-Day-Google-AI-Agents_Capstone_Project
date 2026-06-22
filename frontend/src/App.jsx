import { useEffect, useState } from "react";
import { api } from "./api";
import MetricCard from "./components/MetricCard";
import AnomalyList from "./components/AnomalyList";
import IncidentHistory from "./components/IncidentHistory";
import TrendChart from "./components/TrendChart";
import AgentChat from "./components/AgentChat";
import StatusBar from "./components/StatusBar";

export default function App() {
  const [metrics, setMetrics] = useState(null);
  const [trends, setTrends] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [health, setHealth] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthData, metricsData, trendsData, incidentsData, analysis] =
        await Promise.all([
          api.health(),
          api.metrics(),
          api.trends(15),
          api.incidents(),
          api.analyze(),
        ]);
      setHealth(healthData);
      setMetrics(metricsData);
      setTrends(trendsData);
      setIncidents(incidentsData);
      setAnomalies(analysis?.agent_response?.anomalies || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, []);

  const cpu = metrics?.system?.get_cpu_metrics?.cpu_percent;
  const memory = metrics?.system?.get_memory_metrics?.percent;
  const disk = metrics?.system?.get_disk_metrics?.partitions?.[0]?.percent;

  return (
    <div className="app">
      <header>
        <h1>Server Health Monitoring Agent</h1>
        <button onClick={refresh} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      {error && <div className="error">{error}</div>}

      <StatusBar health={health} metrics={metrics} />

      <section className="cards">
        <MetricCard title="CPU" value={cpu} unit="%" />
        <MetricCard title="Memory" value={memory} unit="%" />
        <MetricCard title="Disk" value={disk} unit="%" />
        <MetricCard
          title="Tools OK"
          value={metrics?.success_count}
          unit={`/ ${metrics?.tool_count || 0}`}
        />
      </section>

      <div className="grid">
        <TrendChart trends={trends} />
        <AnomalyList anomalies={anomalies} summaries={trends?.summaries || []} />
        <IncidentHistory incidents={incidents} />
        <AgentChat />
      </div>
    </div>
  );
}
