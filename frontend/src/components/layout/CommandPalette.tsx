import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Search,
  X,
  FileText,
  FolderLock,
  FileBarChart,
  GitBranch,
  Shield,
  Settings,
  PlusCircle,
  ExternalLink,
  History,
  Command,
  ArrowRight,
  TrendingUp,
} from "lucide-react";

interface SearchResult {
  id: string;
  type: "investigation" | "evidence" | "report" | "action" | "navigation";
  title: string;
  subtitle: string;
  badge?: string;
  status?: string;
  url: string;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

const STATIC_NAVIGATION: SearchResult[] = [
  {
    id: "nav-cases",
    type: "navigation",
    title: "Cases & Active Dossiers",
    subtitle: "Navigate to primary case dashboard",
    badge: "NAV",
    url: "/",
  },
  {
    id: "nav-investigations",
    type: "navigation",
    title: "AI Reasoning Graph",
    subtitle: "Multi-agent LangGraph execution graph",
    badge: "NAV",
    url: "/investigations",
  },
  {
    id: "nav-evidence",
    type: "navigation",
    title: "Evidence Vault",
    subtitle: "Cryptographic SHA-256 evidence chain",
    badge: "NAV",
    url: "/evidence",
  },
  {
    id: "nav-analytics",
    type: "navigation",
    title: "Financial Analytics",
    subtitle: "Real-time KPIs and risk aggregations",
    badge: "NAV",
    url: "/analytics",
  },
  {
    id: "nav-reports",
    type: "navigation",
    title: "Regulatory & Executive Reports",
    subtitle: "FinCEN SAR generator and PDF dossiers",
    badge: "NAV",
    url: "/reports",
  },
  {
    id: "nav-admin",
    type: "navigation",
    title: "Admin Console",
    subtitle: "Role management and cluster diagnostics",
    badge: "ADMIN",
    url: "/admin",
  },
  {
    id: "nav-profile",
    type: "navigation",
    title: "User Profile & Security",
    subtitle: "Investigator credentials and preferences",
    badge: "USER",
    url: "/profile",
  },
];

const QUICK_ACTIONS: SearchResult[] = [
  {
    id: "act-create-case",
    type: "action",
    title: "New Investigation Case",
    subtitle: "Initiate LangGraph multi-agent analysis for a transaction",
    badge: "ACTION",
    url: "/",
  },
  {
    id: "act-upload-evidence",
    type: "action",
    title: "Upload Digital Evidence",
    subtitle: "Ingest and hash payload to HSM immutable vault",
    badge: "ACTION",
    url: "/evidence",
  },
  {
    id: "act-generate-sar",
    type: "action",
    title: "Generate FinCEN SAR Filing",
    subtitle: "Draft automated Suspicious Activity Report",
    badge: "ACTION",
    url: "/reports",
  },
  {
    id: "act-check-health",
    type: "action",
    title: "Inspect Worker & Cluster Health",
    subtitle: "View Redis task queue, worker daemon & Postgres telemetry",
    badge: "SYSTEM",
    url: "/admin",
  },
];

const CATEGORIES = ["ALL", "INVESTIGATIONS", "EVIDENCE", "REPORTS", "NAVIGATION", "ACTIONS"];

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("ALL");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  const navigate = useNavigate();
  const inputRef = useRef<HTMLInputElement>(null);

  // Load recent searches from localStorage
  useEffect(() => {
    try {
      const saved = localStorage.getItem("ffire_recent_searches");
      if (saved) {
        setRecentSearches(JSON.parse(saved).slice(0, 5));
      }
    } catch {
      // Ignore localStorage errors
    }
  }, []);

  // Focus input on open
  useEffect(() => {
    if (isOpen) {
      setQuery("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  // Global Keyboard listener for Ctrl+K / Cmd+K and Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        if (isOpen) {
          onClose();
        } else {
          // Open handled by parent or trigger
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Execute search queries
  useEffect(() => {
    const token = localStorage.getItem("token");
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const trimmed = query.trim().toLowerCase();

    // 1. Initial State: Default actions and navigation
    if (!trimmed) {
      let defaults = [...QUICK_ACTIONS, ...STATIC_NAVIGATION];
      if (activeCategory === "NAVIGATION") {
        defaults = STATIC_NAVIGATION;
      } else if (activeCategory === "ACTIONS") {
        defaults = QUICK_ACTIONS;
      }
      setResults(defaults);
      setSelectedIndex(0);
      return;
    }

    // 2. Filter local actions and navigation
    const matchedActions = QUICK_ACTIONS.filter(
      (a) =>
        a.title.toLowerCase().includes(trimmed) ||
        a.subtitle.toLowerCase().includes(trimmed)
    );
    const matchedNav = STATIC_NAVIGATION.filter(
      (n) =>
        n.title.toLowerCase().includes(trimmed) ||
        n.subtitle.toLowerCase().includes(trimmed)
    );

    // 3. Query backend universal search API
    setIsLoading(true);
    const controller = new AbortController();

    const fetchRemote = async () => {
      try {
        const catParam = activeCategory !== "ALL" ? `&category=${activeCategory.toLowerCase()}` : "";
        const res = await fetch(`/api/v1/search/universal?q=${encodeURIComponent(trimmed)}${catParam}`, {
          headers,
          signal: controller.signal,
        });

        let remoteItems: SearchResult[] = [];
        if (res.ok) {
          const data = await res.json();
          remoteItems = data.results || [];
        }

        let combined: SearchResult[] = [];
        if (activeCategory === "ALL") {
          combined = [...remoteItems, ...matchedActions, ...matchedNav];
        } else if (activeCategory === "ACTIONS") {
          combined = matchedActions;
        } else if (activeCategory === "NAVIGATION") {
          combined = matchedNav;
        } else {
          combined = remoteItems;
        }

        setResults(combined);
        setSelectedIndex(0);
      } catch (err: any) {
        if (err.name !== "AbortError") {
          // Fallback to local filtering
          setResults([...matchedActions, ...matchedNav]);
        }
      } finally {
        setIsLoading(false);
      }
    };

    const timer = setTimeout(fetchRemote, 150);

    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, activeCategory]);

  // Global Escape key listener when modal is active
  useEffect(() => {
    if (!isOpen) return;
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, [isOpen, onClose]);

  const selectItem = (item: SearchResult) => {
    // Record query in recent searches
    if (query.trim()) {
      const updated = [query.trim(), ...recentSearches.filter((s) => s !== query.trim())].slice(0, 5);
      setRecentSearches(updated);
      try {
        localStorage.setItem("ffire_recent_searches", JSON.stringify(updated));
      } catch {}
    }

    onClose();
    navigate(item.url);
  };

  // Keyboard navigation within modal
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (results.length > 0 ? (prev + 1) % results.length : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (results.length > 0 ? (prev - 1 + results.length) % results.length : 0));
    } else if (e.key === "Enter" && results[selectedIndex]) {
      e.preventDefault();
      selectItem(results[selectedIndex]);
    } else if (e.key === "Escape") {
      e.preventDefault();
      onClose();
    }
  };

  if (!isOpen) return null;

  const getItemIcon = (type: SearchResult["type"]) => {
    switch (type) {
      case "investigation":
        return <GitBranch size={16} className="text-amber-400 shrink-0" />;
      case "evidence":
        return <FolderLock size={16} className="text-emerald-400 shrink-0" />;
      case "report":
        return <FileBarChart size={16} className="text-cyan-400 shrink-0" />;
      case "action":
        return <PlusCircle size={16} className="text-purple-400 shrink-0" />;
      case "navigation":
      default:
        return <FileText size={16} className="text-blue-400 shrink-0" />;
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-[#081425] border border-[#45464d] rounded-xl shadow-2xl shadow-black/80 overflow-hidden flex flex-col font-sans"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        {/* Search Header Bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-[#45464d]/60 bg-[#0c1a30] gap-3">
          <Search size={18} className="text-[#FCD34D] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Search cases, evidence, reports, actions or press ⌘K..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 bg-transparent border-none text-[#d8e3fb] placeholder:text-[#728299] focus:outline-none text-base font-normal"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="text-[#728299] hover:text-[#d8e3fb] p-1 rounded transition-colors"
            >
              <X size={16} />
            </button>
          )}
          <span className="hidden sm:inline-block px-1.5 py-0.5 text-[11px] font-mono text-[#728299] bg-[#111c2d] border border-[#45464d] rounded">
            ESC
          </span>
        </div>

        {/* Category Chips Bar */}
        <div className="flex items-center gap-1 px-4 py-2 bg-[#060f1c] border-b border-[#45464d]/40 overflow-x-auto custom-scrollbar">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`px-2.5 py-1 text-xs font-semibold rounded transition-all whitespace-nowrap ${
                activeCategory === cat
                  ? "bg-[#FCD34D] text-black shadow-sm"
                  : "text-[#728299] hover:text-[#d8e3fb] hover:bg-[#111c2d]"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Recent Searches Pills (if query is empty and recents exist) */}
        {!query && recentSearches.length > 0 && (
          <div className="px-4 py-2 border-b border-[#45464d]/30 bg-[#060f1c]/50 flex items-center gap-2 overflow-x-auto">
            <History size={13} className="text-[#728299] shrink-0" />
            <span className="text-[11px] font-mono text-[#728299] uppercase tracking-wider">Recent:</span>
            {recentSearches.map((s, idx) => (
              <button
                key={idx}
                onClick={() => setQuery(s)}
                className="px-2 py-0.5 text-xs text-[#bec6e0] bg-[#111c2d] hover:bg-[#1a293f] rounded border border-[#45464d]/50 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Results List */}
        <div className="max-h-96 overflow-y-auto custom-scrollbar p-2 space-y-1">
          {isLoading ? (
            <div className="py-8 text-center text-xs font-mono text-[#728299]">
              Searching FFIRE indexed knowledge...
            </div>
          ) : results.length === 0 ? (
            <div className="py-8 text-center space-y-1">
              <p className="text-sm font-semibold text-[#bec6e0]">No matching records found</p>
              <p className="text-xs text-[#728299]">Try searching for case ID, transaction hash, or report title</p>
            </div>
          ) : (
            results.map((item, index) => {
              const isSelected = index === selectedIndex;
              return (
                <div
                  key={item.id}
                  onClick={() => selectItem(item)}
                  onMouseEnter={() => setSelectedIndex(index)}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-lg cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-[#111c2d] border border-[#FCD34D]/40 text-[#d8e3fb]"
                      : "hover:bg-[#0c182a] text-[#c6c6cd] border border-transparent"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="p-1.5 bg-[#081425] rounded border border-[#45464d]/50">
                      {getItemIcon(item.type)}
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-[#d8e3fb] truncate">
                          {item.title}
                        </span>
                        {item.badge && (
                          <span className="px-1.5 py-0.2 text-[10px] font-mono rounded font-bold uppercase bg-[#1a293f] text-[#FCD34D] border border-[#FCD34D]/30">
                            {item.badge}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-[#728299] truncate mt-0.5">
                        {item.subtitle}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    {item.status && (
                      <span className="hidden sm:inline-block text-[11px] font-mono text-[#bec6e0]">
                        {item.status}
                      </span>
                    )}
                    <ArrowRight
                      size={14}
                      className={`transition-transform ${isSelected ? "text-[#FCD34D] translate-x-1" : "text-[#45464d]"}`}
                    />
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer Hotkeys Reference */}
        <div className="flex items-center justify-between px-4 py-2.5 border-t border-[#45464d]/60 bg-[#060f1c] text-[11px] font-mono text-[#728299]">
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-[#111c2d] border border-[#45464d] rounded text-[10px]">↑↓</kbd> Navigate
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-[#111c2d] border border-[#45464d] rounded text-[10px]">↵</kbd> Select
            </span>
            <span className="flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-[#111c2d] border border-[#45464d] rounded text-[10px]">ESC</kbd> Close
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-[#FCD34D]">
            <Command size={12} />
            <span>Universal Palette v2.4</span>
          </div>
        </div>
      </div>
    </div>
  );
}
