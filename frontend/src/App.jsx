import { useState, useEffect } from "react";
import { getAccessToken, startPKCELogin, logout } from "./utils/pkce";
import { api } from "./utils/api";
import TaskList from "./components/TaskList";
import AdminPanel from "./components/AdminPanel";

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState("tasks");

  useEffect(() => {
    const token = getAccessToken();
    if (token) {
      api.getMe()
        .then(setUser)
        .catch(() => { /* expired token */ })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  if (loading) return <div className="center"><div className="spinner" /></div>;

  if (!user) {
    return (
      <div className="landing">
        <div className="landing-card">
          <div className="logo">✓</div>
          <h1>TaskManager</h1>
          <p>Aplikacja zabezpieczona OAuth 2.0 + PKCE<br />z Authentik jako Authorization Server</p>
          <button className="btn-primary" onClick={startPKCELogin}>
            Zaloguj się
          </button>
        </div>
      </div>
    );
  }

  const isAdmin = user.groups?.includes("admin");

  return (
    <div className="app">
      <header>
        <div className="header-inner">
          <span className="brand">✓ TaskManager</span>
          <nav>
            <button
              className={`nav-btn ${view === "tasks" ? "active" : ""}`}
              onClick={() => setView("tasks")}
            >
              Moje zadania
            </button>
            {isAdmin && (
              <button
                className={`nav-btn ${view === "admin" ? "active" : ""}`}
                onClick={() => setView("admin")}
              >
                Panel admina
              </button>
            )}
          </nav>
          <div className="user-info">
            <span>{user.preferred_username || user.email}</span>
            {isAdmin && <span className="badge">admin</span>}
            <button className="btn-logout" onClick={logout}>Wyloguj</button>
          </div>
        </div>
      </header>

      <main>
        {view === "tasks" && <TaskList />}
        {view === "admin" && isAdmin && <AdminPanel />}
      </main>
    </div>
  );
}
