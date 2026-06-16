import { useState, useEffect } from "react";
import { api } from "../utils/api";

const STATUS_LABELS = { todo: "Do zrobienia", in_progress: "W toku", done: "Gotowe" };
const STATUS_COLORS = { todo: "#6366f1", in_progress: "#f59e0b", done: "#10b981" };

export default function TaskList() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [desc, setDesc] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = () => api.listTasks().then(setTasks).catch(setError).finally(() => setLoading(false));

  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!title.trim()) return;
    await api.createTask({ title, description: desc });
    setTitle(""); setDesc("");
    load();
  };

  const cycle = async (task) => {
    const next = { todo: "in_progress", in_progress: "done", done: "todo" };
    await api.updateTask(task.id, { status: next[task.status] });
    load();
  };

  const remove = async (id) => {
    await api.deleteTask(id);
    load();
  };

  if (loading) return <div className="center"><div className="spinner" /></div>;
  if (error) return <div className="error">Błąd: {error.message}</div>;

  return (
    <div className="panel">
      <h2>Moje zadania</h2>

      <div className="form-row">
        <input
          placeholder="Tytuł zadania…"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
        />
        <input
          placeholder="Opis (opcjonalny)"
          value={desc}
          onChange={(e) => setDesc(e.target.value)}
        />
        <button className="btn-primary" onClick={add}>Dodaj</button>
      </div>

      {tasks.length === 0 && (
        <p className="empty">Brak zadań. Dodaj pierwsze!</p>
      )}

      <ul className="task-list">
        {tasks.map((t) => (
          <li key={t.id} className="task-item">
            <div className="task-left">
              <span
                className="status-dot"
                style={{ background: STATUS_COLORS[t.status] }}
                title={STATUS_LABELS[t.status]}
              />
              <div>
                <strong>{t.title}</strong>
                {t.description && <p className="task-desc">{t.description}</p>}
              </div>
            </div>
            <div className="task-actions">
              <button className="btn-sm" onClick={() => cycle(t)}>
                {STATUS_LABELS[t.status]}
              </button>
              <button className="btn-danger-sm" onClick={() => remove(t.id)}>✕</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
