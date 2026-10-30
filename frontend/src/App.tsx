import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { Investigations } from "./pages/Investigations";
import { InvestigationDetails } from "./pages/InvestigationDetails";
import { useAuthStore } from "./store/useAuthStore";
import { Admin, Analytics, EvidenceLibrary, Help, Profile, Reports, Auth, Landing, Pricing } from "./pages";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }
  return <>{children}</>;
}

function App() {
  return (
    <Routes>
      <Route path="/auth" element={<Auth />} />
      <Route path="/landing" element={<Landing />} />
      <Route path="/pricing" element={<Pricing />} />
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/investigations" element={<Investigations />} />
        <Route path="/investigations/:id" element={<InvestigationDetails />} />
        <Route path="/evidence" element={<EvidenceLibrary />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/admin" element={<Admin />} />
        <Route path="/help" element={<Help />} />
        <Route path="/feed" element={<div className="p-8">Real-time Feed (WIP)</div>} />
        <Route path="/settings" element={<div className="p-8">Settings (WIP)</div>} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
