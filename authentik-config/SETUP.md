# Konfiguracja Authentik

Po uruchomieniu `docker compose up -d` Authentik będzie dostępny pod:
- http://localhost:9000  (HTTP)
- https://localhost:9443 (HTTPS)

## 1. Pierwsze uruchomienie

Przejdź na http://localhost:9000/if/flow/initial-setup/
Ustaw hasło dla konta `akadmin`.

## 2. Utwórz aplikację OAuth2

Zaloguj się do Admin UI: http://localhost:9000/if/admin/

### 2a. Utwórz Provider

Nawiguj: **Applications -> Providers -> Create**
- Type: **OAuth2/OpenID Provider**
- Name: `taskmanager-provider`
- Authentication flow: `default-authentication-flow`
- Authorization flow: `default-provider-authorization-implicit-consent`
- Client type: Public (brak client_secret - wymagane dla PKCE)
- Client ID: `taskmanager-client`
- Redirect URIs:
  ```
  http://localhost:3000/callback
  http://localhost:5173/callback
  ```
- Signing Key: wybierz domyślny klucz RS256
- **Scopes**: openid, email, profile
- **Subject mode**: Based on the User's hashed ID
- **Client Type**: Public

### 2b. Utwórz Application

**Applications -> Applications -> Create**
- Name: `Task Manager`
- Slug: `taskmanager`  <- musi się zgadzać z URL-ami w kodzie
- Provider: `taskmanager-provider`

### 2c. Utwórz grupę admin

**Directory -> Groups -> Create**
- Name: `admin`

### 2d. Dodaj property mapping dla grup

**Customization -> Property Mappings -> Create**
- Type: Scope Mapping
- Name: `groups-scope`
- Scope name: `groups`
- Expression:
```python
return list(request.user.ak_groups.values_list("name", flat=True))
```

Wróć do Providera i dodaj `groups-scope` do Selected scopes.

### 2e. Utwórz użytkowników

**Directory -> Users -> Create**
- Normalny: username=`user1`, email=`user1@example.com`
- Admin: username=`admin1`, email=`admin1@example.com` -> przypisz do grupy `admin`

## 3. Sprawdź JWKS

```bash
curl http://localhost:9000/application/o/taskmanager/jwks/
```

Backend używa tych kluczy do weryfikacji JWT bez potrzeby kontaktowania się z Authentik przy każdym żądaniu.

## 4. Testowanie

```bash
# Health (publiczny)
curl http://localhost:8000/health

# Chroniony bez tokena → 403
curl http://localhost:8000/tasks/

# Z tokenem (uzyskanym przez PKCE flow w przeglądarce)
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/users/me
curl -H "Authorization: Bearer <access_token>" http://localhost:8000/tasks/

# Admin (wymaga grupy admin)
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/admin/stats
```
