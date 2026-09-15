import { afterEach, describe, expect, it, vi } from "vitest";

describe("apiClient", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("strips a trailing slash from VITE_API_BASE_URL to avoid double-slash requests", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://example.onrender.com/");
    vi.resetModules();
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const { apiRequest } = await import("../../src/services/apiClient");
    await apiRequest("/api/auth/login");

    expect(fetchMock).toHaveBeenCalledWith(
      "https://example.onrender.com/api/auth/login",
      expect.anything(),
    );
  });

  it("still works when VITE_API_BASE_URL has no trailing slash", async () => {
    vi.stubEnv("VITE_API_BASE_URL", "https://example.onrender.com");
    vi.resetModules();
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ok: true }),
    });
    globalThis.fetch = fetchMock as unknown as typeof fetch;

    const { apiRequest } = await import("../../src/services/apiClient");
    await apiRequest("/api/auth/login");

    expect(fetchMock).toHaveBeenCalledWith(
      "https://example.onrender.com/api/auth/login",
      expect.anything(),
    );
  });
});
