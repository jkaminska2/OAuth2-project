import { getAccessToken } from "./pkce";

const API_URL = import.meta.env.VITE_API_URL;

async function request(path, options = {}) {
  const token = getAccessToken();
  const resp = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

export const api = {
  listTasks: () => request("/tasks/"),
  createTask: (data) => request("/tasks/", { method: "POST", body: JSON.stringify(data) }),
  updateTask: (id, data) => request(`/tasks/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTask: (id) => request(`/tasks/${id}`, { method: "DELETE" }),

  getMe: () => request("/users/me"),

  getStats: () => request("/admin/stats"),
  getAllTasks: () => request("/admin/tasks"),

  health: () => fetch(`${API_URL}/health`).then((r) => r.json()),
};
