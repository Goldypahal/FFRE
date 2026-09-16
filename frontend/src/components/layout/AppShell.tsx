import React, { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { CommandPalette } from "./CommandPalette";

export function AppShell() {
  const [isPaletteOpen, setIsPaletteOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden font-body-md text-body-md bg-[#081425] text-[#d8e3fb] selection:bg-amber-500 selection:text-black">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Workspace Frame */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#081425] relative overflow-hidden">
        {/* Top Header Bar */}
        <Header onOpenPalette={() => setIsPaletteOpen(true)} />

        {/* Scrollable Main Content Canvas */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6">
          <Outlet />
        </div>
      </main>

      {/* Chapter 41 Universal Command Palette & Global Search */}
      <CommandPalette isOpen={isPaletteOpen} onClose={() => setIsPaletteOpen(false)} />
    </div>
  );
}

