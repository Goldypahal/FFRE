import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "@fontsource-variable/bricolage-grotesque/opsz.css";
import "@fontsource-variable/instrument-sans/wght.css";
import "../Landing/landing.css";
import { useAuthStore } from "../../store/useAuthStore";
import { apiUrl } from "../../lib/api";

interface LoginResponse {
  access_token?: string;
  refresh_token?: string;
  role?: string;
  user_id?: string;
  name?: string;
  mfa_required?: boolean;
  mfa_ticket?: string;
  masked_phone?: string;
  user?: { id?: string; name?: string; role?: string };
  detail?: unknown;
}

function errorText(data: LoginResponse, fallback: string): string {
  return typeof data.detail === "string" ? data.detail : fallback;
}

export function Auth() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mfa, setMfa] = useState<{ ticket: string; maskedPhone: string } | null>(null);
  const [code, setCode] = useState("");
  const { login } = useAuthStore();
  const navigate = useNavigate();

  // Signs in with what the server says about the account, never with guessed defaults.
  const finishSignIn = (data: LoginResponse) => {
    const id = data.user_id ?? data.user?.id;
    const role = data.role ?? data.user?.role;
    if (!data.access_token || !id || !role) {
      throw new Error("The server did not return a complete session. Try again.");
    }
    login(
      data.access_token,
      { id, name: data.name || data.user?.name || email.split("@")[0], email, role },
      remember ? data.refresh_token ?? null : null,
    );
    navigate("/");
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const body = new URLSearchParams();
      body.append("username", email);
      body.append("password", password);

      const res = await fetch(apiUrl("/auth/login"), {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
      });
      const data: LoginResponse = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(errorText(data, "Incorrect username or password"));
      }
      if (data.mfa_required) {
        if (!data.mfa_ticket) throw new Error("The server asked for a verification code but sent no ticket. Try again.");
        setMfa({ ticket: data.mfa_ticket, maskedPhone: data.masked_phone || "your phone" });
        setPassword("");
        return;
      }
      finishSignIn(data);
    } catch (err: any) {
      setError(err.message || "Failed to authenticate");
    } finally {
      setLoading(false);
    }
  };

  const handleMfaSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!mfa) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(apiUrl("/auth/mfa/verify"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ mfa_ticket: mfa.ticket, code: code.trim() }),
      });
      const data: LoginResponse = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(errorText(data, "That code did not match. Check it and try again."));
      }
      finishSignIn(data);
    } catch (err: any) {
      setError(err.message || "Failed to verify the code");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ffl auth-page">
      <aside className="au-l">
        <Link className="mark" to="/landing" aria-label="FFIRE home">
          <svg viewBox="0 0 28 28" width="28" height="28" aria-hidden="true">
            <rect width="28" height="28" rx="8" fill="currentColor" />
            <path d="M8 20V8h11M8 14h8" stroke="var(--surface)" strokeWidth="3" fill="none" strokeLinecap="square" />
          </svg>
          <span>FFIRE</span>
        </Link>
        <div className="au-claim">
          <h2>Every claim checked. Every case replayable.</h2>
          <p>Sign in to review investigations, the evidence behind them and the verdict on every claim.</p>
          <ul>
            <li>Verified against the evidence</li>
            <li className="bad">Contradicted by the evidence</li>
            <li className="gap">Ungrounded, no evidence found</li>
          </ul>
        </div>
        <p className="au-fine">Advisory only. A person authorizes every filing.</p>
      </aside>
      <main className="au-r">
        <div className="au-card">
          <h1>FFIRE Login</h1>
          <p className="au-sub">Financial Fraud Intelligence &amp; Real-time Evaluation</p>
          {mfa ? (
          <form className="au-form" onSubmit={handleMfaSubmit}>
            <p className="au-sub">Enter the code we sent to {mfa?.maskedPhone}.</p>
            {error && (
              <div role="alert" className="au-err">
                {error}
              </div>
            )}
            <div className="fl">
              <label htmlFor="auth-code">Verification code</label>
              <input id="auth-code" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{4,8}" value={code} onChange={(e) => setCode(e.target.value)} required autoFocus />
            </div>
            <button className="au-btn" type="submit" disabled={loading}>
              {loading ? "Verifying…" : "Verify and sign in"}
            </button>
            <button className="au-btn ghost" type="button" onClick={() => { setMfa(null); setCode(""); setError(null); }}>
              Use a different account
            </button>
          </form>
          ) : (
          <form className="au-form" onSubmit={handleAuthSubmit}>
            <button className="au-btn ghost" type="button" disabled title="Single sign-on is not configured for this deployment">
              Continue with SSO
            </button>
            <div className="au-or">or</div>
            {error && (
              <div role="alert" className="au-err">
                {error}
              </div>
            )}
            <div className="fl">
              <label htmlFor="auth-email">Investigator email</label>
              <input id="auth-email" placeholder="name@ffire.internal" type="email" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div className="fl">
              <label htmlFor="auth-password">Password</label>
              <input id="auth-password" placeholder="Your password" type="password" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            <div className="au-row">
              <label htmlFor="remember">
                <input id="remember" type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
                Stay signed in
              </label>
            </div>
            <button className="au-btn" type="submit" disabled={loading}>
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>
          )}
          <p className="au-fine">Access is restricted to authorized personnel. Activity is logged and audited.</p>
          <Link className="au-back" to="/landing">Back to the website</Link>
        </div>
      </main>
    </div>
  );
}
