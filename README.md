# TaskManager – OAuth 2.0 + PKCE

Projekt zaliczeniowy z bezpieczeństwa aplikacji.  
Aplikacja do zarządzania zadaniami zabezpieczona standardem **OAuth 2.0 Authorization Code Flow z PKCE**.

## Stos technologiczny

| Warstwa | Technologia |
|---|---|
| Authorization Server | **Authentik** (nie Keycloak) |
| Backend | **FastAPI** (Python 3.12) + SQLAlchemy async |
| Frontend | **React 18** + Vite |
| Baza danych | **PostgreSQL 16** |
| Cache / Broker | Redis 7 |
| Konteneryzacja | **Docker Compose** z named volumes |
| CI/CD | GitHub Actions |

---

## Jak działa PKCE?

**Proof Key for Code Exchange** (RFC 7636) to rozszerzenie OAuth 2.0 zaprojektowane dla publicznych klientów (SPA, aplikacje mobilne), które nie mogą bezpiecznie przechowywać `client_secret`.

```
Klient (przeglądarka)                   Authentik (Auth Server)
        │                                       │
        │  1. Generuj code_verifier (losowe 32B)│
        │  2. code_challenge = SHA-256(verifier)│
        │                                       │
        │──── GET /authorize                ────▶│
        │     ?code_challenge=<hash>            │
        │     &code_challenge_method=S256       │
        │     &response_type=code               │
        │                                       │
        │◀─── Redirect z ?code=AUTH_CODE ───────│
        │                                       │
        │──── POST /token ───────────────────▶  │
        │     code=AUTH_CODE                    │
        │     code_verifier=<oryginał>          │
        │                                       │
        │     Authentik weryfikuje:             │
        │     SHA-256(verifier) == challenge?   │
        │                                       │
        │◀─── access_token (JWT) ───────────────│
```

**Dlaczego to bezpieczne?**  
Nawet jeśli atakujący przechwyci `code` (np. przez referer header lub logi serwera), nie zna `code_verifier`, więc nie może wymienić kodu na token.

---

## Struktura projektu

```
oauth2-project/
├── docker-compose.yml          # Orkiestracja wszystkich serwisów
├── .env.example                # Szablon zmiennych środowiskowych
├── db/
│   └── init.sql                # Inicjalizacja bazy (tworzy DB dla Authentik)
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app, CORS, routery
│   │   ├── config.py           # Ustawienia (pydantic-settings)
│   │   ├── database.py         # Async SQLAlchemy engine
│   │   ├── models.py           # Model Task
│   │   ├── middleware/
│   │   │   └── auth.py         # Weryfikacja JWT + JWKS + require_role()
│   │   └── routers/
│   │       ├── health.py       # GET /health  ← PUBLICZNY
│   │       ├── tasks.py        # CRUD /tasks/ ← 4× CHRONIONE
│   │       ├── users.py        # GET /users/me ← CHRONIONY
│   │       └── admin.py        # /admin/*  ← CHRONIONE + ROLA admin
│   ├── alembic/                # Migracje bazy
│   ├── tests/
│   │   └── test_api.py         # Testy automatyczne (pytest-asyncio)
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── utils/
│   │   │   ├── pkce.js         # Implementacja PKCE (verifier, challenge, exchange)
│   │   │   └── api.js          # Klient HTTP do backendu
│   │   ├── components/
│   │   │   ├── TaskList.jsx    # Widok zadań użytkownika
│   │   │   └── AdminPanel.jsx  # Panel admina (widoczny tylko dla roli admin)
│   │   ├── pages/
│   │   │   └── CallbackPage.jsx # Obsługuje redirect po logowaniu
│   │   └── App.jsx
│   ├── Dockerfile
│   └── nginx.conf
├── authentik-config/
│   └── SETUP.md                # Instrukcja konfiguracji Authentik
└── .github/
    └── workflows/
        └── ci.yml              # GitHub Actions CI/CD
```

---

## Endpointy API

| Metoda | Ścieżka | Auth | Rola | Opis |
|---|---|---|---|---|
| GET | `/health` | ❌ Brak | — | Health check (publiczny) |
| GET | `/users/me` | ✅ Bearer | — | Info o zalogowanym użytkowniku |
| GET | `/tasks/` | ✅ Bearer | — | Lista zadań użytkownika |
| POST | `/tasks/` | ✅ Bearer | — | Utwórz zadanie |
| PATCH | `/tasks/{id}` | ✅ Bearer | — | Zaktualizuj zadanie |
| DELETE | `/tasks/{id}` | ✅ Bearer | — | Usuń zadanie |
| GET | `/admin/stats` | ✅ Bearer | **admin** | Statystyki wszystkich użytkowników |
| GET | `/admin/tasks` | ✅ Bearer | **admin** | Wszystkie zadania w systemie |

---

## Szybki start

### 1. Sklonuj i skopiuj .env

```bash
git clone <repo-url> && cd oauth2-project
cp .env.example .env
```

### 2. Uruchom wszystkie serwisy

```bash
docker compose up -d
```

Poczekaj ~30 sekund na inicjalizację Authentik.

### 3. Skonfiguruj Authentik

Otwórz http://localhost:9000/if/flow/initial-setup/ i postępuj zgodnie z:

```
authentik-config/SETUP.md
```

Kluczowe kroki:
- Utwórz Provider (Public, Client ID: `taskmanager-client`)
- Utwórz Application (slug: `taskmanager`)
- Dodaj Property Mapping dla grup
- Utwórz użytkownika i opcjonalnie przypisz do grupy `admin`

### 4. Otwórz aplikację

- **Frontend**: http://localhost:3000
- **Backend API docs**: http://localhost:8000/docs
- **Authentik Admin**: http://localhost:9000/if/admin/

### 5. Uruchom testy

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
AUTHENTIK_JWKS_URL="http://localhost:9000/application/o/taskmanager/jwks/" \
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (osobny terminal)
cd frontend
npm install
npm run dev
# Dostępny na http://localhost:5173
```

---

## Wymagania spełnione

### Na 3.0
- [x] Backend zabezpieczony OAuth 2.0 (JWT Bearer)
- [x] 4 chronione endpointy (`/tasks/` ×4)
- [x] 1 endpoint uwzględniający role (`/admin/stats` wymaga grupy `admin`)
- [x] 1 niezabezpieczony endpoint (`/health`)
- [x] Frontend korzystający z backendu (React + Vite)
- [x] Baza danych (PostgreSQL z async SQLAlchemy)
- [x] Authorization Server (Authentik)
- [x] PKCE włączone (implementacja w `frontend/src/utils/pkce.js`)

### Na wyższą ocenę
- [x] Docker Compose z named volumes dla wszystkich serwisów
- [x] **Authentik** zamiast Keycloak jako Authorization Server
- [x] Testy automatyczne (pytest-asyncio, 10 testów)
- [x] CI/CD (GitHub Actions – testy + build Docker)
- [x] Volumes dla Authentik (`authentik_media`, `authentik_templates`)

---

## Wyjaśnienie PKCE (na obronę)

**Q: Co to jest `code_verifier`?**  
A: Losowy ciąg 32 bajtów zakodowany w base64url (43-128 znaków). Generowany przez klienta i przechowywany w `sessionStorage` tylko do momentu wymiany kodu.

**Q: Co to jest `code_challenge`?**  
A: `BASE64URL(SHA-256(code_verifier))`. Wysyłany do auth servera przy żądaniu autoryzacji. Nie pozwala odtworzyć `code_verifier`.

**Q: Dlaczego `S256` a nie `plain`?**  
A: `S256` używa SHA-256, więc nawet przechwycenie `code_challenge` nie ujawnia `code_verifier`. `plain` jest podatny na atak gdy atakujący może obserwować żądanie autoryzacji.

**Q: Gdzie jest client_secret?**  
A: Nie ma go. Provider jest skonfigurowany jako **Public** w Authentik. PKCE zastępuje client_secret dla publicznych klientów.

**Q: Co weryfikuje backend?**  
A: Backend pobiera JWKS z Authentik i weryfikuje podpis JWT (RS256), issuer oraz expiry. Nie dzwoni do Authentik przy każdym żądaniu – weryfikacja jest lokalna.
