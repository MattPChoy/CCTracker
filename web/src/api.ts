// Tiny fetch wrapper. Token lives in localStorage; sent as Bearer on every call.

const TOKEN_KEY = "cctracker_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(t: string | null) {
  if (t) localStorage.setItem(TOKEN_KEY, t);
  else localStorage.removeItem(TOKEN_KEY);
}

async function req<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(path, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface Membership {
  board_id: string;
  slug: string;
  name: string;
  role: string;
}
export interface Me {
  handle: string;
  memberships: Membership[];
}
export interface PerModel {
  model: string;
  label: string;
  total_tokens: number;
  output_tokens: number;
  cost_usd: number | null;
  share: number;
}
export interface Entry {
  rank: number;
  handle: string;
  value: number;
  cost_usd: number | null;
  per_model: PerModel[];
}
export interface Board {
  id: string;
  slug: string;
  name: string;
  invite_code?: string | null;
  visibility: string;
  default_metric: string;
  default_window: string;
  show_cost: boolean;
}
export interface Leaderboard {
  board: Board | null;
  metric: string;
  window: string;
  entries: Entry[];
}

export const api = {
  register: (handle?: string) =>
    req<{ handle: string; token: string; prefix: string }>("POST", "/v1/users", {
      handle: handle || undefined,
    }),
  me: () => req<Me>("GET", "/v1/me"),
  updateMe: (body: { handle: string }) => req<Me>("PATCH", "/v1/me", body),
  createBoard: (name: string) => req<Board>("POST", "/v1/boards", { name }),
  getBoard: (id: string) => req<Board>("GET", `/v1/boards/${id}`),
  joinBoard: (id: string, invite_code: string) =>
    req<Board>("POST", `/v1/boards/${id}/join`, { invite_code }),
  leaderboard: (id: string, metric?: string, window?: string) => {
    const q = new URLSearchParams();
    if (metric) q.set("metric", metric);
    if (window) q.set("window", window);
    return req<Leaderboard>("GET", `/v1/boards/${id}/leaderboard?${q}`);
  },
  publicLeaderboard: (metric?: string, window?: string) => {
    const q = new URLSearchParams();
    if (metric) q.set("metric", metric);
    if (window) q.set("window", window);
    return req<Leaderboard>("GET", `/v1/public/leaderboard?${q}`);
  },
};
