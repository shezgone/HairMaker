import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Direct import - module-level fetch mock must be properly managed
import {
  login,
  register,
  createSession,
  getSession,
  getStyles,
  startSimulation,
  getSimulationStatus,
  uploadPhoto,
  deleteStyle,
  updateNotes,
  getMe,
} from "@/lib/api";

function ok(data: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
    statusText: "OK",
  } as Response;
}

function err(status: number, detail: string): Response {
  return {
    ok: false,
    status,
    json: () => Promise.resolve({ detail }),
    statusText: "Error",
  } as Response;
}

describe("API functions", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn();
    global.fetch = fetchMock as typeof fetch;
    window.localStorage.setItem("access_token", "test-token");
    // Remove refresh token to avoid auto-refresh side effects
    window.localStorage.removeItem("refresh_token");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ─── Auth ───

  it("login sends correct request and returns tokens", async () => {
    const resp = { access_token: "tok", refresh_token: "ref", user: { id: "1" } };
    fetchMock.mockResolvedValueOnce(ok(resp));

    const result = await login("test@test.com", "Test1234");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/auth/login");
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body.email).toBe("test@test.com");
    expect(body.password).toBe("Test1234");
    expect(result.access_token).toBe("tok");
  });

  it("login throws on 401", async () => {
    fetchMock.mockResolvedValue(err(401, "이메일 또는 비밀번호가 올바르지 않습니다."));
    await expect(login("bad@test.com", "wrong")).rejects.toThrow();
  });

  it("register sends correct request", async () => {
    const resp = { access_token: "tok", refresh_token: "ref", user: { id: "1" } };
    fetchMock.mockResolvedValueOnce(ok(resp));

    const result = await register("new@test.com", "Test1234", "테스트", "살롱");

    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/auth/register");
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body.email).toBe("new@test.com");
    expect(body.name).toBe("테스트");
    expect(body.salon_name).toBe("살롱");
    expect(result.access_token).toBe("tok");
  });

  it("getMe sends bearer token", async () => {
    fetchMock.mockResolvedValueOnce(ok({ user: { id: "1", name: "테스트" } }));
    const result = await getMe("my-token");

    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer my-token");
    expect(result.user.id).toBe("1");
  });

  // ─── Sessions ───

  it("createSession sends gender", async () => {
    fetchMock.mockResolvedValueOnce(ok({ id: "sess-1", gender: "female" }));
    const result = await createSession("female");

    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body.gender).toBe("female");
    expect(result.id).toBe("sess-1");
  });

  it("getSession fetches by ID", async () => {
    fetchMock.mockResolvedValueOnce(ok({ id: "sess-1", status: "active" }));
    const result = await getSession("sess-1");

    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/sessions/sess-1");
    expect(result.id).toBe("sess-1");
  });

  it("updateNotes sends PATCH with notes", async () => {
    fetchMock.mockResolvedValueOnce(ok({ id: "sess-1", consultation_notes: "메모" }));
    await updateNotes("sess-1", "메모");

    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/sessions/sess-1/notes");
    expect(fetchMock.mock.calls[0][1].method).toBe("PATCH");
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body.consultation_notes).toBe("메모");
  });

  // ─── Styles ───

  it("getStyles fetches with filters", async () => {
    fetchMock.mockResolvedValueOnce(ok({ styles: [], total: 0 }));
    const result = await getStyles({ face_shape: "oval" });

    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/styles");
    expect(fetchMock.mock.calls[0][0]).toContain("face_shape=oval");
    expect(result.total).toBe(0);
  });

  it("deleteStyle sends DELETE", async () => {
    fetchMock.mockResolvedValueOnce(ok({ detail: "삭제되었습니다." }));
    const result = await deleteStyle("style-1");

    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/styles/style-1");
    expect(fetchMock.mock.calls[0][1].method).toBe("DELETE");
    expect(result.detail).toBe("삭제되었습니다.");
  });

  // ─── Simulation ───

  it("startSimulation sends correct body", async () => {
    fetchMock.mockResolvedValueOnce(ok({ job_id: "job-1", status: "pending" }));
    const result = await startSimulation("sess-1", "style-1", "flux");

    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/simulate");
    const body = JSON.parse(fetchMock.mock.calls[0][1].body);
    expect(body.session_id).toBe("sess-1");
    expect(body.style_id).toBe("style-1");
    expect(body.model).toBe("flux");
    expect(result.job_id).toBe("job-1");
  });

  it("getSimulationStatus returns status", async () => {
    fetchMock.mockResolvedValueOnce(ok({ job_id: "job-1", status: "done", result_url: "url" }));
    const result = await getSimulationStatus("job-1");

    expect(result.status).toBe("done");
    expect(result.result_url).toBe("url");
  });

  // ─── Upload ───

  it("uploadPhoto sends FormData", async () => {
    fetchMock.mockResolvedValueOnce(ok({ photo_url: "https://example.com/photo.jpg" }));

    const blob = new Blob(["fake"], { type: "image/jpeg" });
    const result = await uploadPhoto("sess-1", blob);

    expect(fetchMock.mock.calls[0][0]).toContain("/api/v1/sessions/sess-1/photo");
    expect(fetchMock.mock.calls[0][1].method).toBe("POST");
    expect(fetchMock.mock.calls[0][1].body).toBeInstanceOf(FormData);
    expect(result.photo_url).toBe("https://example.com/photo.jpg");
  });

  it("uploadPhoto throws on error", async () => {
    fetchMock.mockResolvedValueOnce(err(413, "파일 크기가 10MB를 초과합니다."));

    const blob = new Blob(["fake"], { type: "image/jpeg" });
    await expect(uploadPhoto("sess-1", blob)).rejects.toThrow("파일 크기가 10MB를 초과합니다.");
  });

  // ─── Auth Headers ───

  it("includes Authorization header from localStorage", async () => {
    window.localStorage.setItem("access_token", "my-token");
    fetchMock.mockResolvedValueOnce(ok({ id: "sess-1" }));

    await getSession("sess-1");

    expect(fetchMock.mock.calls[0][1].headers.Authorization).toBe("Bearer my-token");
  });
});
