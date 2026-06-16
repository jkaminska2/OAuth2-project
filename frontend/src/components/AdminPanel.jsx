import { useState, useEffect } from "react";
import { api } from "../utils/api";

export default function AdminPanel() {
  const [stats, setStats] = useState(null);
  const [allTasks, setAllTasks] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([api.getStats(), api.getAllTasks()])
      .then(([s, t]) => { setStats(s); setAllTasks(t); })
      .catch(setError);
  }, []);

  if (error) return <div className="error">Brak dostępu lub błąd: {error.message}</div>;
  if (!stats) return <div className="center"><div className="spinner" /></div>;

  return (
    <div className="panel">
      <h2>Panel administratora</h2>
      <p className="hint">Ten widok jest dostępny tylko dla grupy <code>admin</code> w Authentik.</p>

      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-value">{stats.total_tasks}</span>
          <span className="stat-label">Wszystkich zadań</span>
        </div>
        {Object.entries(stats.by_status || {}).map(([s, n]) => (
          <div key={s} className="stat-card">
            <span className="stat-value">{n}</span>
            <span className="stat-label">{s}</span>
          </div>
        ))}
      </div>

      <h3>Wszystkie zadania ({allTasks.length})</h3>
      <table className="admin-table">
        <thead>
          <tr><th>ID</th><th>Tytuł</th><th>Status</th><th>Właściciel</th></tr>
        </thead>
        <tbody>
          {allTasks.map((t) => (
            <tr key={t.id}>
              <td>{t.id}</td>
              <td>{t.title}</td>
              <td>{t.status}</td>
              <td className="sub">{t.owner_sub}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
