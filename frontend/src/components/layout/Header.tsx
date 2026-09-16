import React from "react";
import { Search, Bell, Settings } from "lucide-react";
import { Link } from "react-router-dom";

interface HeaderProps {
  title?: string;
  onSearch?: (query: string) => void;
  onOpenPalette?: () => void;
  rightContent?: React.ReactNode;
}

export function Header({ title, onSearch, onOpenPalette, rightContent }: HeaderProps) {
  return (
    <header className="h-16 flex items-center justify-between px-6 bg-[#081425] border-b border-[#45464d] shrink-0 font-sans w-full z-20">
      {/* Brand & Search */}
      <div className="flex items-center gap-6">
        <Link to="/" className="font-headline-md text-2xl font-bold text-[#FCD34D] tracking-tight">
          FFIRE
        </Link>
        <div
          onClick={onOpenPalette}
          className="hidden lg:flex items-center justify-between bg-[#111c2d] hover:bg-[#152338] border border-[#45464d] hover:border-[#FCD34D]/60 rounded-lg px-3 py-1.5 w-80 cursor-pointer transition-all group"
        >
          <div className="flex items-center min-w-0">
            <Search size={15} className="text-[#c6c6cd] group-hover:text-[#FCD34D] mr-2.5 shrink-0 transition-colors" />
            <span className="text-sm text-[#728299] group-hover:text-[#d8e3fb] truncate select-none">
              Universal Search & Commands...
            </span>
          </div>
          <kbd className="text-[10px] font-mono px-1.5 py-0.5 bg-[#081425] border border-[#45464d] rounded text-[#bec6e0] select-none ml-2 shrink-0">
            ⌘K
          </kbd>
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
