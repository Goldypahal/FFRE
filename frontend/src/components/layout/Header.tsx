import React from "react";
import { Search, Bell, Settings, LogOut } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useAuthStore } from "../../store/useAuthStore";
import { signOut } from "../../lib/api";

interface HeaderProps {
  title?: string;
  onSearch?: (query: string) => void;
  onOpenPalette?: () => void;
  rightContent?: React.ReactNode;
}

export function Header({ title, onSearch, onOpenPalette, rightContent }: HeaderProps) {
  const user = useAuthStore((s) => s.user);
  const navigate = useNavigate();
  const initials = (user?.name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");

  const handleSignOut = async () => {
    await signOut();
    navigate("/auth");
  };

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
            <p className="font-label-md text-sm text-[#d8e3fb] font-semibold leading-none">{user?.name || "Signed in"}</p>
            <p className="font-label-sm text-[10px] text-[#728299] uppercase tracking-tighter mt-1 font-mono">
              {user?.role || ""}
            </p>
          </div>
          <div
            aria-hidden="true"
            className="w-9 h-9 rounded-full border border-[#45464d] group-hover:border-[#FCD34D] transition-all flex items-center justify-center text-sm font-semibold text-[#d8e3fb]"
          >
            {initials}
          </div>
        </Link>
        <button
          type="button"
          onClick={handleSignOut}
          className="text-[#c6c6cd] hover:text-white transition-colors p-1 cursor-pointer"
          aria-label="Sign out"
          title="Sign out"
        >
          <LogOut size={18} />
        </button>
      </div>
    </header>
  );
}
