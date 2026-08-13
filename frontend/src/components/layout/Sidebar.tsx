import React from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "../../lib/utils";
import {
  FileText,
  GitBranch,
  FolderLock,
  History,
  Activity,
  Plus,
  HelpCircle,
  Headphones,
} from "lucide-react";

const NAV_ITEMS = [
  { name: "Cases", path: "/", icon: FileText },
  { name: "Reasoning Graph", path: "/investigations", icon: GitBranch },
  { name: "Evidence Vault", path: "/evidence", icon: FolderLock },
  { name: "Historical Patterns", path: "/analytics", icon: History },
  { name: "System Health", path: "/reports", icon: Activity },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="hidden md:flex flex-col h-full w-64 bg-[#040e1f] border-r border-[#45464d] py-6 shrink-0 font-sans">
      {/* Brand Header */}
      <div className="px-6 mb-8">
        <h1 className="font-headline-md text-2xl font-bold text-[#d8e3fb] tracking-tight">FFIRE Engine</h1>
        <p className="font-label-sm text-xs text-[#728299] mt-1 font-mono">V2.4 Active</p>
      </div>

      {/* Primary Navigation */}
      <nav className="flex-1 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive =
            location.pathname === item.path ||
            (item.path !== "/" && location.pathname.startsWith(item.path));
          const Icon = item.icon;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex items-center px-6 py-3 font-label-md text-xs uppercase tracking-wider transition-all border-r-4",
                isActive
                  ? "bg-[#0f172a] text-[#bec6e0] border-[#bec6e0] font-semibold"
                  : "text-[#c6c6cd] hover:bg-[#111c2d] border-transparent"
              )}
            >
              <Icon size={18} className="mr-3 shrink-0" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Action Button */}
      <div className="px-4 mb-6">
        <Link
          to="/investigations"
          className="w-full py-3 bg-[#b7c8e1] text-[#213145] font-label-md text-xs font-bold tracking-widest uppercase rounded flex items-center justify-center gap-2 hover:bg-white transition-all shadow-md active:scale-95 text-center"
        >
          <Plus size={16} /> NEW INVESTIGATION
        </Link>
      </div>

      {/* Footer Support Links */}
      <div className="mt-auto border-t border-[#45464d]/40 pt-4">
        <Link
          to="/help"
          className="flex items-center px-6 py-2 text-[#c6c6cd] hover:text-[#d8e3fb] transition-colors font-label-sm text-xs font-mono"
        >
          <HelpCircle size={16} className="mr-3" /> Documentation
        </Link>
        <Link
          to="/help"
          className="flex items-center px-6 py-2 text-[#c6c6cd] hover:text-[#d8e3fb] transition-colors font-label-sm text-xs font-mono"
        >
          <Headphones size={16} className="mr-3" /> Support
        </Link>
      </div>
    </aside>
  );
}
