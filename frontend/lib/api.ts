import type { Session, HairStyle, SimulationJob } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || "API request failed");
  }
  return res.json();
}

// Sessions
export const createSession = (salon_id: string, designer_id: string, gender: "male" | "female") =>
  apiFetch<Session>("/api/v1/sessions", {
    method: "POST",
    body: JSON.stringify({ salon_id, designer_id, gender }),
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
  const res = await fetch(`${API_BASE}/api/v1/sessions/${sessionId}/photo`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Photo upload failed");
  return res.json();
}

// Styles
export const getStyles = (params?: { face_shape?: string; tags?: string }) =>
  apiFetch<{ styles: HairStyle[]; total: number }>(
    `/api/v1/styles?${new URLSearchParams(params as Record<string, string> || {}).toString()}`
  );

export const getStyle = (styleId: string) =>
  apiFetch<HairStyle>(`/api/v1/styles/${styleId}`);

// Simulation
export const startSimulation = (session_id: string, style_id: string, model: "flux" | "flux-max" = "flux") =>
  apiFetch<{ job_id: string; status: string }>("/api/v1/simulate", {
    method: "POST",
    body: JSON.stringify({ session_id, style_id, model }),
  });

export const getSimulationStatus = (jobId: string) =>
  apiFetch<SimulationJob>(`/api/v1/simulate/${jobId}`);

// SSE: Face analysis stream
export function createAnalysisStream(sessionId: string): EventSource {
  return new EventSource(`${API_BASE}/api/v1/sessions/${sessionId}/analysis`);
}
