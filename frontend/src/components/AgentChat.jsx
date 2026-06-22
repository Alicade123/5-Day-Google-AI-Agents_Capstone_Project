import { useState } from "react";
import { api } from "../api";

export default function AgentChat() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const result = await api.query(query);
      setResponse(result);
    } catch (err) {
      setResponse({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="panel chat">
      <h2>Agent Chat</h2>
      <form onSubmit={submit}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Why is server performance degrading?"
        />
        <button type="submit" disabled={loading}>
          {loading ? "..." : "Ask"}
        </button>
      </form>
      {response?.error && <p className="error">{response.error}</p>}
      {response && !response.error && (
        <div className="agent-response">
          <section>
            <h4>Facts</h4>
            <ul>{response.facts?.map((f, i) => <li key={i}>{f}</li>)}</ul>
          </section>
          <section>
            <h4>Possible explanations</h4>
            <ul>{response.possible_explanations?.map((e, i) => <li key={i}>{e}</li>)}</ul>
          </section>
          <p><strong>Confidence:</strong> {response.confidence}</p>
          <section>
            <h4>Recommended actions</h4>
            <ul>{response.recommended_actions?.map((a, i) => <li key={i}>{a}</li>)}</ul>
          </section>
        </div>
      )}
    </div>
  );
}
