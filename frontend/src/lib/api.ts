import { useAuthStore } from "../store/useAuthStore";

// Dynamically resolve API URL: supports runtime injection, vite env, or relative reverse proxy in production
const API_BASE_URL =
  (typeof window !== "undefined" && (window as any).__FFRE_CONFIG__?.API_BASE_URL) ||
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== "undefined" && window.location.port !== "5173" ? "/api/v1" : "http://127.0.0.1:8000/api/v1");

/** Build a full URL for an API path such as "/reports/123/download". */
export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`;
}

let refreshInFlight: Promise<boolean> | null = null;

/** Exchange the stored refresh token for a new pair. Concurrent callers share one request. */
function refreshSession(): Promise<boolean> {
  if (refreshInFlight) return refreshInFlight;
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return Promise.resolve(false);
  refreshInFlight = fetch(apiUrl("/auth/refresh"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })
    .then(async (res) => {
      if (!res.ok) return false;
      const data = await res.json();
      if (!data.access_token) return false;
      useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
      return true;
    })
    .catch(() => false)
    .finally(() => {
      refreshInFlight = null;
    });
  return refreshInFlight;
}

/**
 * fetch() against the API with the bearer token attached. On a 401 it refreshes the session once
 * and retries; if that fails the local session is cleared, which sends the user to the sign-in page.
 */
export async function authFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const send = () => {
    const token = useAuthStore.getState().token;
    const headers = new Headers(options.headers);
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (!headers.has("Content-Type") && options.body !== undefined && !(options.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }
    return fetch(apiUrl(path), { ...options, headers });
  };

  let response = await send();
  const hadSession = Boolean(useAuthStore.getState().token);
  if (response.status === 401 && hadSession && !path.startsWith("/auth/")) {
    if (await refreshSession()) {
      response = await send();
    }
    if (response.status === 401) {
      useAuthStore.getState().logout();
    }
  }
  return response;
}

/** Revoke the session on the server, then clear it locally. Local sign-out happens even if the call fails. */
export async function signOut(): Promise<void> {
  const token = useAuthStore.getState().token;
  try {
    if (token) {
      await fetch(apiUrl("/auth/logout"), { method: "POST", headers: { Authorization: `Bearer ${token}` } });
    }
  } catch {
    // Offline or server down: the local session is still cleared below.
  } finally {
    useAuthStore.getState().logout();
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await authFetch(path, options);

  if (!response.ok) {
    let errorDetail = "API Error";
    try {
      const errData = await response.json();
      if (typeof errData.detail === "string") errorDetail = errData.detail;
    } catch {
      // ignore
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  get: <T>(path: string, options?: RequestInit) =>
    request<T>(path, { ...options, method: "GET" }),
  post: <T>(path: string, body?: any, options?: RequestInit) =>
    request<T>(path, {
      ...options,
      method: "POST",
      body: body instanceof FormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
    }),
  put: <T>(path: string, body?: any, options?: RequestInit) =>
    request<T>(path, {
      ...options,
      method: "PUT",
      body: body instanceof FormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
    }),
  patch: <T>(path: string, body?: any, options?: RequestInit) =>
    request<T>(path, {
      ...options,
      method: "PATCH",
      body: body instanceof FormData ? body : (body !== undefined ? JSON.stringify(body) : undefined),
    }),
  delete: <T>(path: string, options?: RequestInit) =>
    request<T>(path, { ...options, method: "DELETE" }),
};
