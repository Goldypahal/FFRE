import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Bell, Settings, Download, SlidersHorizontal, ChevronDown, ShieldCheck } from "lucide-react";

export function TopNav() {
  const location = useLocation();

  const NAV_TABS = [
    { name: "Dashboard", path: "/" },
    { name: "Analytics", path: "/analytics" },
    { name: "Investment", path: "/investigations" },
    { name: "Activity", path: "/evidence" },
    { name: "Saving", path: "/reports" },
  ];

  // Helper for active page subtitle
  const getPageInfo = () => {
    switch (location.pathname) {
      case "/analytics":
        return { title: "Analytics Overview", sub: "Deep financial risk intelligence and AI metrics" };
      case "/investigations":
        return { title: "Investigations Summary", sub: "Active case portfolio and anomaly tracking" };
      case "/evidence":
        return { title: "Evidence & Activity", sub: "Audit trails, hardware signals and transaction history" };
      case "/reports":
        return { title: "Reports & Savings", sub: "Automated fraud prevention loss recovery reports" };
      default:
        return { title: "Sales Overview", sub: "Your Current sales summary and activity" };
    }
  };

  const { title, sub } = getPageInfo();

  return (
    <header className="w-full flex flex-col gap-6 p-4 md:p-6 lg:p-8 pb-4 bg-transparent">
      {/* Top Header Row */}
      <div className="flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#635BFF] via-[#7C3AED] to-[#A855F7] flex items-center justify-center shadow-lg shadow-purple-500/30 border border-white/20">
            <ShieldCheck className="w-6 h-6 text-white" />
          </div>
          <span className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-1">
            Ledger<span className="text-purple-400 font-extrabold">X</span>
          </span>
        </div>

        {/* Capsule Navigation Bar */}
        <nav className="hidden md:flex items-center bg-[#13162B]/90 border border-white/10 rounded-full p-1.5 backdrop-blur-md shadow-inner">
          {NAV_TABS.map((tab) => {
            const isActive =
              location.pathname === tab.path ||
              (tab.path !== "/" && location.pathname.startsWith(tab.path));
            return (
              <Link
                key={tab.path}
                to={tab.path}
                className={`px-5 py-2 rounded-full text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? "bg-[#635BFF] text-white shadow-lg shadow-purple-500/30"
                    : "text-slate-400 hover:text-white hover:bg-white/5"
                }`}
              >
                {tab.name}
              </Link>
            );
          })}
        </nav>

        {/* Right Header Control Icons */}
        <div className="flex items-center gap-3 md:gap-4">
          {/* Notification Bell */}
          <button className="relative w-10 h-10 rounded-full bg-[#13162B] border border-white/10 flex items-center justify-center text-slate-300 hover:text-white hover:border-white/20 transition-all">
            <Bell size={18} />
            <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-red-500 ring-2 ring-[#080A15]"></span>
          </button>

          {/* Settings Icon */}
          <button className="w-10 h-10 rounded-full bg-[#13162B] border border-white/10 flex items-center justify-center text-slate-300 hover:text-white hover:border-white/20 transition-all">
            <Settings size={18} />
          </button>

          {/* User Avatar */}
          <div className="relative cursor-pointer group">
            <img
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80"
              alt="User Avatar"
              className="w-10 h-10 rounded-full object-cover border-2 border-purple-500/40 group-hover:border-purple-400 transition-all shadow-md"
            />
            <span className="absolute bottom-0 right-0 w-3 h-3 rounded-full bg-emerald-500 border-2 border-[#080A15]"></span>
          </div>
        </div>
      </div>

      {/* Sub-Header Banner (Sales Overview + Actions) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-1">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">{title}</h1>
          <p className="text-slate-400 text-xs md:text-sm mt-0.5">{sub}</p>
        </div>

        {/* Action Pills */}
        <div className="flex items-center gap-2.5 flex-wrap sm:flex-nowrap">
          {/* Dropdown Pill */}
          <button className="ledger-pill-btn px-4 py-2 rounded-full text-xs md:text-sm font-medium flex items-center gap-2">
            This Month <ChevronDown size={14} className="text-slate-400" />
          </button>

          {/* Export Button Pill */}
          <button className="ledger-pill-btn px-4 py-2 rounded-full text-xs md:text-sm font-medium flex items-center gap-2">
            <Download size={15} /> Export
          </button>

          {/* Filter Primary Pill */}
          <button className="px-5 py-2 rounded-full text-xs md:text-sm font-medium bg-[#635BFF] text-white flex items-center gap-2 shadow-lg shadow-purple-500/25 hover:bg-[#5249EA] transition-all">
            <SlidersHorizontal size={15} /> Filter
          </button>
        </div>
      </div>
    </header>
  );
}
