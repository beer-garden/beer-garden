import { beforeEach, describe, expect, it, vi } from "vitest";

import { ClearToken, GetAuthHeaders, GetToken, UserLogin } from "./token_service";

// Mock jwt-decode to return a valid payload without needing a real JWT token
vi.mock("jwt-decode", () => ({
  jwtDecode: vi.fn((token: string) => {
    // Parse the token payload from base64 if possible, otherwise return defaults
    try {
      const parts = token.split(".");
      if (parts.length >= 2) {
        const payload = JSON.parse(atob(parts[1]));
        return payload;
      }
    } catch {
      // fall through
    }
    return { username: "test", preferences: {} };
  }),
}));

// Mock the util_service dependency
vi.mock("./util_service", () => ({
  GetBaseURL: vi.fn(() => ""),
  ChangePowerUser: vi.fn(),
  ChangeTheme: vi.fn(),
  ClearThemes: vi.fn(),
  GetAuthHeaders: vi.fn(() => new Headers()),
}));

describe("token_service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe("GetToken", () => {
    it("returns null when no token in localStorage", () => {
      expect(GetToken()).toBeNull();
    });

    it("returns the token from localStorage", () => {
      localStorage.setItem("token", "my-test-token");
      expect(GetToken()).toBe("my-test-token");
    });
  });

  describe("ClearToken", () => {
    it("removes the token from localStorage", () => {
      localStorage.setItem("token", "my-test-token");
      ClearToken();
      expect(localStorage.getItem("token")).toBeNull();
    });

    it("does not throw when token is not present", () => {
      expect(() => ClearToken()).not.toThrow();
    });
  });

  describe("GetAuthHeaders", () => {
    it("returns headers with auth token when token exists", () => {
      localStorage.setItem("token", "my-test-token");
      const headers = GetAuthHeaders();
      expect(headers.get("Authorization")).toBe("Bearer my-test-token");
    });

    it("returns headers without auth when no token", () => {
      const headers = GetAuthHeaders();
      expect(headers.get("Authorization")).toBeNull();
    });
  });

  describe("UserLogin", () => {
    it("stores token and refresh on successful login", async () => {
      const mockResponse = {
        ok: true,
        json: () => ({
          access: "access-token",
          refresh: "refresh-token",
        }),
      };
      globalThis.fetch = vi.fn().mockResolvedValue(mockResponse);

      await UserLogin("testuser", "password123");

      expect(localStorage.getItem("token")).toBe("access-token");
      expect(localStorage.getItem("refresh")).toBe("refresh-token");
      expect(fetch).toHaveBeenCalledWith("/api/v1/token", {
        headers: expect.any(Headers),
        method: "POST",
        body: JSON.stringify({
          username: "testuser",
          password: "password123",
        }),
      });
    });

    it("throws on non-ok response", async () => {
      const mockResponse = {
        ok: false,
        status: 401,
        json: () => ({}),
      };
      globalThis.fetch = vi.fn().mockResolvedValue(mockResponse);

      await expect(UserLogin("bad", "creds")).rejects.toThrow(
        "HTTP error: Status 401",
      );
      expect(localStorage.getItem("token")).toBeNull();
    });

    it("passes through custom headers", async () => {
      const mockResponse = {
        ok: true,
        json: () => ({ access: "tok" }),
      };
      globalThis.fetch = vi.fn().mockResolvedValue(mockResponse);

      await UserLogin("user", "pass", { "X-Custom": "value" });

      expect(fetch).toHaveBeenCalledWith(
        "/api/v1/token",
        expect.objectContaining({
          headers: expect.any(Headers),
        }),
      );
    });
  });
});
