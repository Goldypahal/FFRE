import { useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { Investigations } from "./pages/Investigations";
import { InvestigationDetails } from "./pages/InvestigationDetails";
import { useAuthStore } from "./store/useAuthStore";
import { Admin, Analytics, EvidenceLibrary, Help, Profile, Reports, Auth, Landing, Pricing } from "./pages";

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

function App() {
  const { login } = useAuthStore();

  useEffect(() => {
    // Auto login logic from previous App.tsx
    const authenticate = async () => {
      try {
        const regRes = await fetch(`${API_BASE_URL}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name: 'Demo Analyst', email: 'analyst@ffire.ai', password: 'securepassword123', role: 'investigator' })
        });
        
        let tokenData;
        if (regRes.ok) {
          tokenData = await regRes.json();
        } else {
          const params = new URLSearchParams();
          params.append('username', 'analyst@ffire.ai');
          params.append('password', 'securepassword123');
          
          const loginRes = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: params
          });
          if (loginRes.ok) {
            tokenData = await loginRes.json();
          }
        }
        
        if (tokenData && tokenData.access_token) {
          login(tokenData.access_token, {
            id: '1',
            name: 'Demo Analyst',
            email: 'analyst@ffire.ai',
            role: 'investigator'
          });
        }
      } catch (err) {
        console.error("Auth error:", err);
      }
    };
    authenticate();
  }, [login]);

  return (
    <Routes>
      <Route path="/auth" element={<Auth />} />
      <Route path="/landing" element={<Landing />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route element={<AppShell />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/investigations" element={<Investigations />} />
        <Route path="/investigations/:id" element={<InvestigationDetails />} />
        <Route path="/evidence" element={<EvidenceLibrary />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/help" element={<Help />} />
        {/* Placeholder routes */}
        <Route path="/feed" element={<div className="p-8">Real-time Feed (WIP)</div>} />
        <Route path="/settings" element={<div className="p-8">Settings (WIP)</div>} />
      </Route>
    </Routes>
  );
}

export default App;

