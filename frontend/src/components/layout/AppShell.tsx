import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden font-body-md text-body-md bg-[#081425] text-[#d8e3fb] selection:bg-amber-500 selection:text-black">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Workspace Frame */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#081425] relative overflow-hidden">
        {/* Top Header Bar */}
        <Header />

        {/* Scrollable Main Content Canvas */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
