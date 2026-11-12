import { create } from "zustand";

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string, user: User, refreshToken?: string | null) => void;
  /** Replace the tokens after a refresh, keeping the signed-in user. */
  setTokens: (token: string, refreshToken?: string | null) => void;
  /** Clear the local session only. Use signOut() from lib/api to also revoke it on the server. */
  logout: () => void;
}

const TOKEN_KEY = "ffre_token";
const REFRESH_KEY = "ffre_refresh_token";
const USER_KEY = "ffre_user";

function read(key: string): string | null {
  try {
    return typeof window !== "undefined" ? localStorage.getItem(key) : null;
  } catch {
    return null;
  }
}

function write(key: string, value: string | null) {
  try {
    if (typeof window === "undefined") return;
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    // Storage can be unavailable (private mode); the in-memory session still works.
  }
}

const savedToken = read(TOKEN_KEY);
const savedRefresh = read(REFRESH_KEY);
const savedUserStr = read(USER_KEY);
let savedUser: User | null = null;

if (savedUserStr) {
  try {
    savedUser = JSON.parse(savedUserStr);
  } catch {
    // Ignore parse errors
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  token: savedToken,
  refreshToken: savedRefresh,
  user: savedUser,
  isAuthenticated: Boolean(savedToken && savedUser),
  login: (token, user, refreshToken = null) => {
    write(TOKEN_KEY, token);
    write(REFRESH_KEY, refreshToken);
    write(USER_KEY, JSON.stringify(user));
    set({ token, refreshToken, user, isAuthenticated: true });
  },
  setTokens: (token, refreshToken) => {
    write(TOKEN_KEY, token);
    if (refreshToken) write(REFRESH_KEY, refreshToken);
    set((s) => ({ token, refreshToken: refreshToken || s.refreshToken }));
  },
  logout: () => {
    write(TOKEN_KEY, null);
    write(REFRESH_KEY, null);
    write(USER_KEY, null);
    set({ token: null, refreshToken: null, user: null, isAuthenticated: false });
  },
}));
