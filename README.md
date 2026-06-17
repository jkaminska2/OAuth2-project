# TaskManager - OAuth 2.0 + PKCE

Autor: Joanna Kamińska. 

Projekt zaliczeniowy z bezpieczeństwa aplikacji webowych.
Aplikacja do zarządzania zadaniami zabezpieczona standardem OAuth 2.0 Authorization Code Flow z PKCE.

| Warstwa | Technologia |
|---|---|
| Authorization Server | **Authentik** |
| Backend | **FastAPI** (Python 3.12) + SQLAlchemy async |
| Frontend | **React 18** + Vite |
| Baza danych | **PostgreSQL 16** |
| Cache / Broker | Redis 7 |
| Konteneryzacja | **Docker Compose** z named volumes |
| CI/CD | GitHub Actions |

---


## Endpointy API

| Metoda | Ścieżka | Auth | Rola | Opis |
|---|---|---|---|---|
| GET | `/health` | Brak | - | Health check (publiczny) |
| GET | `/users/me` | Bearer | - | Info o zalogowanym użytkowniku |
| GET | `/tasks/` | Bearer | - | Lista zadań użytkownika |
| POST | `/tasks/` | Bearer | - | Utwórz zadanie |
| PATCH | `/tasks/{id}` | Bearer | - | Zaktualizuj zadanie |
| DELETE | `/tasks/{id}` | Bearer | - | Usuń zadanie |
| GET | `/admin/stats` | Bearer | admin | Statystyki wszystkich użytkowników |
| GET | `/admin/tasks` | Bearer | admin | Wszystkie zadania w systemie |

---

## Szybki start

### 1. Kopiowanie .env

```bash
cp .env.example .env
```

### 2. Uruchamianie wszystkich serwisów

```bash
docker compose up -d
```


### 3. Konfiguracja Authentik

Otwórz http://localhost:9000/if/flow/initial-setup/ i postępuj zgodnie z:

```
authentik-config/SETUP.md
```

Kluczowe kroki:
- Utwórz Provider (Public, Client ID: `taskmanager-client`)
- Utwórz Application (slug: `taskmanager`)
- Dodaj Property Mapping dla grup
- Utwórz użytkownika i opcjonalnie przypisz do grupy `admin`

### 4. Otwieranie aplikacji

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Authentik Admin: http://localhost:9000/if/admin/

### 5. Uruchamianie testów

```bash
cd backend
pip install -r requirements.txt aiosqlite
pytest tests/ -v
```

---

## Uruchamianie bez Dockera (development)

```bash
# Backend
cd backend
pip install -r requirements.txt
DATABASE_URL="postgresql+asyncpg://postgres:secret@localhost:5432/appdb" \
AUTHENTIK_ISSUER="http://localhost:9000/application/o/taskmanager/" \
AUTHENTIK_JWKS_URL="http://authentik-server:9000/application/o/taskmanager/jwks/" \
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (osobny terminal)
cd frontend
npm install
npm run dev
# Dostępny na http://localhost:5173
```
