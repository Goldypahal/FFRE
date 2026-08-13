import React from "react";
import { Search, Bell, Settings } from "lucide-react";
import { Link } from "react-router-dom";

interface HeaderProps {
  title?: string;
  onSearch?: (query: string) => void;
  rightContent?: React.ReactNode;
}

export function Header({ title, onSearch, rightContent }: HeaderProps) {
  return (
    <header className="h-16 flex items-center justify-between px-6 bg-[#081425] border-b border-[#45464d] shrink-0 font-sans w-full z-20">
      {/* Brand & Search */}
      <div className="flex items-center gap-6">
        <Link to="/" className="font-headline-md text-2xl font-bold text-[#FCD34D] tracking-tight">
          FFIRE
        </Link>
        <div className="hidden lg:flex items-center bg-[#111c2d] border border-[#45464d] rounded px-3 py-1.5 w-80">
          <Search size={15} className="text-[#c6c6cd] mr-2 shrink-0" />
          <input
            type="text"
            placeholder="Search signals, cases, or tools..."
            className="bg-transparent border-none focus:outline-none text-sm text-[#d8e3fb] w-full placeholder:text-[#909097]"
            onChange={(e) => onSearch && onSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-5">
        {rightContent}
        <div className="flex items-center gap-3 border-r border-[#45464d] pr-5">
          <button className="text-[#c6c6cd] hover:text-white transition-colors p-1 cursor-pointer">
            <Bell size={18} />
          </button>
          <button className="text-[#c6c6cd] hover:text-white transition-colors p-1 cursor-pointer">
            <Settings size={18} />
          </button>
        </div>

        {/* User Profile */}
        <Link to="/profile" className="flex items-center gap-3 cursor-pointer group">
          <div className="text-right hidden sm:block">
            <p className="font-label-md text-sm text-[#d8e3fb] font-semibold leading-none">Alex Chen</p>
            <p className="font-label-sm text-[10px] text-[#728299] uppercase tracking-tighter mt-1 font-mono">
              Sr. Investigator
            </p>
          </div>
          <img
            src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80"
            alt="Alex Chen"
            className="w-9 h-9 rounded-full object-cover border border-[#45464d] group-hover:border-[#FCD34D] transition-all"
          />
        </Link>
      </div>
    </header>
  );
}
