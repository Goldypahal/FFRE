import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/useAuthStore";

export function Auth() {
  const [email, setEmail] = useState("analyst@ffire.ai");
  const [password, setPassword] = useState("securepassword123");
  const [remember, setRemember] = useState(true);
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simulate auto-login or store dispatch
    setTimeout(() => {
      login("demo-access-token-12345", {
        id: "1",
        name: "Demo Analyst",
        email,
        role: "investigator",
      });
      setLoading(false);
      navigate("/");
    }, 600);
  };

  return (
    <body className="font-body-md text-body-md min-h-screen flex flex-col items-center justify-center p-gutter relative overflow-hidden dark">
      {/* Atmospheric Background Animation */}

      {/* Top Glow / Identity */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-px bg-gradient-to-r from-transparent via-investigation-gold/30 to-transparent"></div>
      <main className="w-full max-w-md relative z-10">
        {/* Logo & Branding */}
        <div className="flex flex-col items-center mb-stack-lg">
          <div className="mb-stack-sm p-3 bg-surface-container-high rounded-xl border border-outline-variant shadow-lg">
            {/* Using a simple div as placeholder for the security icon since we don't have the exact material icon */}
            <div className="w-9 h-9 bg-investigation-gold/10 rounded-full flex items-center justify-center mb-3">
              <span className="text-investigation-gold font-bold text-2xl">🛡️</span>
            </div>
          </div>
          <h1 className="font-headline-lg text-headline-lg text-on-surface tracking-tight">FFIRE Login</h1>
          <p className="font-body-sm text-body-sm text-on-surface-variant mt-1">
            Financial Fraud Intelligence & Real-time Evaluation
          </p>
        </div>
        {/* Auth Card */}
        <div className="login-card p-8 border border-outline-variant rounded-xl shadow-2xl backdrop-blur-sm">
          <form className="space-y-stack-md" onSubmit={handleAuthSubmit}>
            {/* SSO Section (Enterprise Mandate) */}
            <button className="w-full flex items-center justify-center gap-stack-sm bg-surface-container-highest hover:bg-surface-bright text-on-surface border border-outline font-label-md text-label-md py-3 rounded-lg transition-all active:scale-95" type="button">
              {/* Using a div as placeholder for the fingerprint icon */}
              <div className="flex items-center">
                <span className="mr-2">🔒</span>
                CONTINUE WITH SSO
              </div>
            </button>
            <div className="relative flex items-center py-stack-sm">
              <div className="flex-grow border-t border-outline-variant"></div>
              <span className="flex-shrink mx-4 font-label-sm text-label-sm text-on-surface-variant uppercase tracking-widest">OR</span>
              <div className="flex-grow border-t border-outline-variant"></div>
            </div>
            {/* Manual Credentials */}
            <div className="space-y-stack-sm">
              <div>
                <label className="block font-label-sm text-label-sm text-on-surface-variant mb-1 uppercase tracking-tight">Investigator Email</label>
                <div className="relative">
                  {/* Using a div as placeholder for the email icon */}
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center">
                    <span className="mr-1">📧</span>
                  </div>
                  <input className="w-full pl-10 pr-4 py-2.5 bg-surface-dim border border-outline rounded-lg text-on-surface font-body-sm placeholder:text-outline/50 focus:ring-0 focus:border-investigation-gold input-focus-ring transition-all outline-none" placeholder="name@ffire.internal" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                </div>
              </div>
              <div>
                <div className="flex justify-between items-end mb-1">
                  <label className="block font-label-sm text-label-sm text-on-surface-variant uppercase tracking-tight">Secure Token / Password</label>
                  <a className="font-label-sm text-label-sm text-tertiary hover:text-investigation-gold transition-colors" href="#">Forgot?</a>
                </div>
                <div className="relative">
                  {/* Using a div as placeholder for the lock icon */}
                  <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center">
                    <span className="mr-1">🔐</span>
                  </div>
                  <input className="w-full pl-10 pr-4 py-2.5 bg-surface-dim border border-outline rounded-lg text-on-surface font-body-sm placeholder:text-outline/50 focus:ring-0 focus:border-investigation-gold input-focus-ring transition-all outline-none" placeholder="••••••••••••" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input className="w-4 h-4 rounded border-outline bg-surface-dim text-investigation-gold focus:ring-investigation-gold" id="remember" type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
              <label className="font-body-sm text-body-sm text-on-surface-variant cursor-pointer" htmlFor="remember">Stay authenticated for this session</label>
            </div>
            <button className="w-full py-3 bg-tertiary hover:bg-tertiary-fixed-dim text-on-tertiary font-headline-md text-headline-md rounded-lg transition-all shadow-[0_0_20px_rgba(252,211,77,0.1)] active:opacity-90" type="submit">
              AUTHORIZE ACCESS
            </button>
          </form>
          <div className="mt-stack-lg pt-stack-md border-t border-outline-variant flex items-start gap-stack-sm">
            {/* Using a div as placeholder for the info icon */}
            <div className="flex items-center">
              <span className="mr-2">ℹ️</span>
            </div>
            <p className="font-body-sm text-body-sm text-on-surface-variant/80 italic leading-snug">
              Access restricted to authorized personnel only. All interactions within this terminal are logged and audited in compliance with FINRA 2024 standards.
            </p>
          </div>
        </div>
        {/* System Architecture Graphics (Subtle) */}
        <div className="mt-gutter flex justify-between gap-stack-md opacity-40 grayscale hover:grayscale-0 transition-all duration-700">
          <div className="flex-1 h-32 rounded-lg border border-outline-variant overflow-hidden bg-surface-container">
            {/* Using a div as placeholder for the first image */}
            <div className="w-full h-full bg-surface-container-low flex items-center justify-center">
              <span className="text-on-surface-variant italic">Neural Network Visualization</span>
            </div>
          </div>
          <div className="flex-1 h-32 rounded-lg border border-outline-variant overflow-hidden bg-surface-container">
            {/* Using a div as placeholder for the second image */}
            <div className="w-full h-full bg-surface-container-low flex items-center justify-center">
              <span className="text-on-surface-variant italic">Data Grid Visualization</span>
            </div>
          </div>
        </div>
      </main>
      {/* Footer Links */}
      <footer className="mt-auto py-stack-lg flex flex-col items-center gap-stack-sm relative z-10">
        <div className="flex gap-stack-lg font-label-sm text-label-sm text-outline">
          <a className="hover:text-on-surface transition-colors flex items-center gap-1">
            {/* Using a div as placeholder for the gavel icon */}
            <div className="flex items-center">
              <span className="mr-1">⚖️</span>
            </div>
            Terms of Service
          </a>
          <a className="hover:text-on-surface transition-colors flex items-center gap-1">
            {/* Using a div as placeholder for the hub icon */}
            <div className="flex items-center">
              <span className="mr-1">🔗</span>
            </div>
            Security Architecture
          </a>
          <a className="hover:text-on-surface transition-colors flex items-center gap-1">
            {/* Using a div as placeholder for the help center icon */}
            <div className="flex items-center">
              <span className="mr-1">❓</span>
            </div>
            System Status
          </a>
        </div>
        <p className="font-label-sm text-label-sm text-on-surface-variant/40 mt-2 uppercase tracking-[0.2em]">
          FFIRE CORE ENGINE v2.4.82-SECURE
        </p>
      </footer>
      {/* Interactive Micro-interaction Script */}
      {/* Note: In a real implementation, we would use useEffect for these event listeners */}
    </body>
  );
}