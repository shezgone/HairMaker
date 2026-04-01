import type { Session, HairStyle, SimulationJob, AuthResponse, AuthUser } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getAuthHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  if (token) {
    return { Authorization: `Bearer ${token}` };
  }
  return {};
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const authHeaders = getAuthHeaders();
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...authHeaders, ...options?.headers },
    ...options,
  });

  // 401 시 토큰 갱신 시도
  if (res.status === 401 && typeof window !== "undefined") {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      // 갱신 성공 시 재시도
      const newAuthHeaders = getAuthHeaders();
      const retryRes = await fetch(`${API_BASE}${path}`, {
        headers: { "Content-Type": "application/json", ...newAuthHeaders, ...options?.headers },
        ...options,
      });
      if (!retryRes.ok) {
        const error = await retryRes.json().catch(() => ({ detail: retryRes.statusText }));
        throw new Error(error.detail || "API request failed");
      }
      return retryRes.json();
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API request failed");
  }
  return res.json();
}

async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return false;

  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return false;

    const data = await res.json();
    localStorage.setItem("access_token", data.access_token);
    if (data.refresh_token) {
      localStorage.setItem("refresh_token", data.refresh_token);
    }
    return true;
  } catch {
    return false;
  }
}

// Auth
export const register = (email: string, password: string, name: string, salon_name: string) =>
  apiFetch<AuthResponse>("/api/v1/auth/register", {
    method: "POST",
    body: JSON.stringify({ email, password, name, salon_name }),
  });

export const login = (email: string, password: string) =>
  apiFetch<AuthResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

export const getMe = (token: string) =>
  apiFetch<{ user: AuthUser }>("/api/v1/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });

export const socialLogin = (access_token: string, refresh_token?: string) =>
  apiFetch<AuthResponse>("/api/v1/auth/social/login", {
    method: "POST",
    body: JSON.stringify({ access_token, refresh_token }),
  });

export const refreshAccessToken = (refresh_token: string) =>
  apiFetch<{ access_token: string; refresh_token: string }>("/api/v1/auth/refresh", {
    method: "POST",
    body: JSON.stringify({ refresh_token }),
  });

// Sessions — salon_id/designer_id are now derived from auth token on backend
export const listSessions = (params?: { status?: string; limit?: number }) =>
  apiFetch<{ sessions: Session[]; total: number }>(
    `/api/v1/sessions?${new URLSearchParams(params as Record<string, string> || {}).toString()}`
  );

export const createSession = (gender: "male" | "female") =>
  apiFetch<Session>("/api/v1/sessions", {
    method: "POST",
    body: JSON.stringify({ gender }),
  });

export const getSession = (sessionId: string) =>
  apiFetch<Session>(`/api/v1/sessions/${sessionId}`);

export const getPhotoSignedUrl = (sessionId: string) =>
  apiFetch<{ signed_url: string }>(`/api/v1/sessions/${sessionId}/photo-signed-url`);

export const updateNotes = (sessionId: string, consultation_notes: string) =>
  apiFetch<Session>(`/api/v1/sessions/${sessionId}/notes`, {
    method: "PATCH",
    body: JSON.stringify({ consultation_notes }),
  });

export const selectStyle = (sessionId: string, style_id: string) =>
  apiFetch<Session>(`/api/v1/sessions/${sessionId}/style`, {
    method: "PATCH",
    body: JSON.stringify({ style_id }),
  });

export const getSessionSummary = (sessionId: string) =>
  apiFetch<{
    session: Session;
    selected_style: HairStyle | null;
    simulation_results: Array<{ job_id: string; result_url: string; style_id: string; status: string }>;
  }>(`/api/v1/sessions/${sessionId}/summary`);

// Photo upload
export async function uploadPhoto(sessionId: string, file: Blob): Promise<{ photo_url: string }> {
  const form = new FormData();
  form.append("file", file, "photo.jpg");
  const authHeaders = getAuthHeaders();
  const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/photo`, {
    method: "POST",
    headers: { ...authHeaders },
    body: form,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "사진 업로드에 실패했습니다.");
  }
  return res.json();
}

// Styles
export const getStyles = (params?: { face_shape?: string; tags?: string; gender?: string }) =>
  apiFetch<{ styles: HairStyle[]; total: number }>(
    `/api/v1/styles?${new URLSearchParams(params as Record<string, string> || {}).toString()}`
  );

export const getStyle = (styleId: string) =>
  apiFetch<HairStyle>(`/api/v1/styles/${styleId}`);

export const createStyle = (data: { name: string; description?: string; gender?: string; hair_length?: string }) =>
  apiFetch<HairStyle>("/api/v1/styles", {
    method: "POST",
    body: JSON.stringify(data),
  });

export const deleteStyle = (styleId: string) =>
  apiFetch<{ detail: string }>(`/api/v1/styles/${styleId}`, {
    method: "DELETE",
  });

// Simulation
export const startSimulation = (session_id: string, style_id: string, model: "flux" | "flux-max" = "flux") =>
  apiFetch<{ job_id: string; status: string }>("/api/v1/simulate", {
    method: "POST",
    body: JSON.stringify({ session_id, style_id, model }),
  });

export const getSimulationStatus = (jobId: string) =>
  apiFetch<SimulationJob>(`/api/v1/simulate/${jobId}`);

// SSE: Face analysis stream (auth token in URL query param since EventSource doesn't support headers)
export function createAnalysisStream(sessionId: string): EventSource {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const url = `${API_BASE}/api/v1/sessions/${sessionId}/analysis`;
  // EventSource doesn't support custom headers, so we pass token as query param
  // The backend also accepts Authorization header from the fetch-based SSE
  return new EventSource(token ? `${url}?token=${encodeURIComponent(token)}` : url);
}
