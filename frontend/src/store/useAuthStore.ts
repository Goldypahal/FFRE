import { create } from "zustand";

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AuthState {
  token: string | null;
  user: User | null;
  isAuthenticated: boolean;
  login: (token: string, user: User) => void;
  logout: () => void;
}

const savedToken = typeof window !== "undefined" ? localStorage.getItem("ffre_token") : null;
const savedUserStr = typeof window !== "undefined" ? localStorage.getItem("ffre_user") : null;
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
  user: savedUser,
  isAuthenticated: Boolean(savedToken && savedUser),
  login: (token, user) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("ffre_token", token);
      localStorage.setItem("ffre_user", JSON.stringify(user));
    }
    set({ token, user, isAuthenticated: true });
  },
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("ffre_token");
      localStorage.removeItem("ffre_user");
    }
    set({ token: null, user: null, isAuthenticated: false });
  },
}));
