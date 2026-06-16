import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { exchangeCodeForToken, saveTokens } from "../utils/pkce";

export default function CallbackPage() {
  const navigate = useNavigate();
  const handled = useRef(false);

  useEffect(() => {
    if (handled.current) return;
    handled.current = true;

    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const state = params.get("state");
    const error = params.get("error");

    if (error) {
      console.error("Auth error:", error, params.get("error_description"));
      navigate("/");
      return;
    }

    if (!code) {
      navigate("/");
      return;
    }

    exchangeCodeForToken(code, state)
      .then((tokens) => {
        saveTokens(tokens);
        navigate("/");
      })
      .catch((err) => {
        console.error("Token exchange error:", err);
        navigate("/");
      });
  }, [navigate]);

  return (
    <div className="center">
      <div className="spinner" />
      <p>Logowanie…</p>
    </div>
  );
}
