/**
 * OAuth 2.0 Authorization Code Flow with PKCE
 *
 * Jak działa PKCE (Proof Key for Code Exchange)?
 * ────────────────────────────────────────────────
 * Problem: w publicznych klientach (SPA, mobile) nie można bezpiecznie
 * przechować client_secret, więc złośliwa aplikacja mogłaby przechwycić
 * authorization code i wymienić go na token.
 *
 * Rozwiązanie PKCE (RFC 7636):
 *  1. Klient generuje losowy `code_verifier` (43-128 znaków, base64url).
 *  2. Oblicza `code_challenge = BASE64URL(SHA-256(code_verifier))`.
 *  3. Wysyła `code_challenge` wraz z żądaniem autoryzacji (widoczne publicznie).
 *  4. Po powrocie z auth servera wysyła `code_verifier` przy wymianie kodu.
 *  5. Auth server weryfikuje: SHA-256(verifier) === challenge → token wydany.
 *
 * Nawet jeśli atakujący przechwyci `code`, nie zna `code_verifier`,
 * więc nie może wymienić kodu na token.
 */

const AUTHENTIK_URL = import.meta.env.VITE_AUTHENTIK_URL;
const CLIENT_ID = import.meta.env.VITE_CLIENT_ID;
const REDIRECT_URI = import.meta.env.VITE_REDIRECT_URI;
const APP_NAME = "taskmanager"; // Authentik application slug

export const AUTH_ENDPOINTS = {
  authorize: `${AUTHENTIK_URL}/application/o/${APP_NAME}/authorize/`,
  token: `${AUTHENTIK_URL}/application/o/${APP_NAME}/token/`,
  userinfo: `${AUTHENTIK_URL}/application/o/${APP_NAME}/userinfo/`,
  logout: `${AUTHENTIK_URL}/application/o/${APP_NAME}/end-session/`,
};

// ── Crypto helpers ─────────────────────────────────────────────────────────────

function base64urlEncode(buffer) {
  return btoa(String.fromCharCode(...new Uint8Array(buffer)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=/g, "");
}

export async function generateCodeVerifier() {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return base64urlEncode(array);
}

export async function generateCodeChallenge(verifier) {
  const encoder = new TextEncoder();
  const data = encoder.encode(verifier);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return base64urlEncode(digest);
}

function generateState() {
  const array = new Uint8Array(16);
  crypto.getRandomValues(array);
  return base64urlEncode(array);
}

// ── PKCE Login ─────────────────────────────────────────────────────────────────

export async function startPKCELogin() {
  const verifier = await generateCodeVerifier();
  const challenge = await generateCodeChallenge(verifier);
  const state = generateState();

  sessionStorage.setItem("pkce_verifier", verifier);
  sessionStorage.setItem("pkce_state", state);

  const params = new URLSearchParams({
    response_type: "code",
    client_id: CLIENT_ID,
    redirect_uri: REDIRECT_URI,
    scope: "openid profile email",
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });

  window.location.href = `${AUTH_ENDPOINTS.authorize}?${params}`;
}

// ── Token exchange ─────────────────────────────────────────────────────────────

export async function exchangeCodeForToken(code, returnedState) {
  const verifier = sessionStorage.getItem("pkce_verifier");
  const savedState = sessionStorage.getItem("pkce_state");

  if (returnedState !== savedState) {
    throw new Error("State mismatch – potential CSRF attack");
  }

  sessionStorage.removeItem("pkce_verifier");
  sessionStorage.removeItem("pkce_state");

  const resp = await fetch(AUTH_ENDPOINTS.token, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      client_id: CLIENT_ID,
      redirect_uri: REDIRECT_URI,
      code,
      code_verifier: verifier,
    }),
  });

  if (!resp.ok) throw new Error(`Token exchange failed: ${resp.status}`);
  return resp.json(); // { access_token, id_token, refresh_token, expires_in }
}

// ── Token storage helpers ──────────────────────────────────────────────────────

export function saveTokens(tokens) {
  localStorage.setItem("access_token", tokens.access_token);
  if (tokens.id_token) localStorage.setItem("id_token", tokens.id_token);
}

export function getAccessToken() {
  return localStorage.getItem("access_token");
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("id_token");
}

export function logout() {
  const idToken = localStorage.getItem("id_token");
  clearTokens();
  const params = new URLSearchParams({
    id_token_hint: idToken || "",
    post_logout_redirect_uri: window.location.origin,
  });
  window.location.href = `${AUTH_ENDPOINTS.logout}?${params}`;
}
