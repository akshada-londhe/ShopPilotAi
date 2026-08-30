/**
 * Auth client helpers — thin wrappers around the Next.js API routes
 * that proxy to the FastAPI backend.  All state lives in the auth context;
 * these functions just handle the fetch + error extraction.
 */

export interface AuthUser {
  user_id: string;
  name: string;
  email: string;
  created_at?: string | null;
}

interface AuthResponse {
  user_id: string;
  name: string;
  email: string;
  token: string;
}

async function fetchJson<T>(url: string, body: object): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    // FastAPI returns { detail: "..." } for HTTP errors
    const msg =
      typeof data?.detail === "string"
        ? data.detail
        : Array.isArray(data?.detail)
          ? data.detail.map((d: { msg: string }) => d.msg).join(", ")
          : "Something went wrong. Please try again.";
    throw new Error(msg);
  }
  return data as T;
}

export async function signUp(
  name: string,
  email: string,
  password: string
): Promise<AuthUser> {
  const data = await fetchJson<AuthResponse>("/api/auth/signup", {
    name,
    email,
    password,
  });
  // Store token in localStorage so we can send it on subsequent requests
  localStorage.setItem("sp_token", data.token);
  return { user_id: data.user_id, name: data.name, email: data.email };
}

export async function signIn(
  email: string,
  password: string
): Promise<AuthUser> {
  const data = await fetchJson<AuthResponse>("/api/auth/signin", {
    email,
    password,
  });
  localStorage.setItem("sp_token", data.token);
  return { user_id: data.user_id, name: data.name, email: data.email };
}

export function signOut(): void {
  localStorage.removeItem("sp_token");
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("sp_token");
}

/** Authorization header with the stored token, or empty if signed out. */
export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getMe(): Promise<AuthUser | null> {
  const token = getToken();
  if (!token) return null;
  try {
    const res = await fetch("/api/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      // Token expired or invalid
      localStorage.removeItem("sp_token");
      return null;
    }
    return (await res.json()) as AuthUser;
  } catch {
    return null;
  }
}
