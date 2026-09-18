import { beforeEach, describe, expect, it, vi } from "vitest";

import * as tokenService from "./token_service";
import {
  CreateUser,
  DeleteUser,
  GetCurrentRoles,
  GetCurrentUser,
  GetUsers,
  UserUpdatePassword,
} from "./user_service";
import * as utilService from "./util_service";

vi.mock("./token_service");
vi.mock("./util_service");

const base64UrlEncode = (str: string): string =>
  btoa(str).replace(/=/g, "").replace(/\+/g, "-").replace(/\//g, "_");

const createMockJWT = (payload: Record<string, unknown>): string => {
  const header = base64UrlEncode(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = base64UrlEncode(JSON.stringify(payload));
  const signature = "mock_signature";
  return `${header}.${body}.${signature}`;
};

const mockToken = createMockJWT({
  username: "testuser",
  preferences: {
    theme: "blue",
    dark_mode: false,
    power_user: false,
  },
  roles: [
    JSON.stringify({ name: "Admin", permission: "GARDEN_ADMIN" }),
    { name: "Operator", permission: "OPERATOR" },
  ],
  exp: Math.floor(Date.now() / 1000) + 3600,
});

describe("user_service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(utilService.GetBaseURL).mockReturnValue("");
    vi.mocked(tokenService.GetAuthHeaders).mockReturnValue(new Headers());
    localStorage.clear();
  });

  describe("GetCurrentUser", () => {
    it("returns username when token has username", () => {
      vi.mocked(tokenService.GetToken).mockReturnValue(mockToken);
      expect(GetCurrentUser()).toBe("testuser");
    });

    it("returns undefined when token is null", () => {
      vi.mocked(tokenService.GetToken).mockReturnValue(null);
      expect(GetCurrentUser()).toBeUndefined();
    });

    it("returns undefined when token has no username", () => {
      const tokenNoUser = createMockJWT({});
      vi.mocked(tokenService.GetToken).mockReturnValue(tokenNoUser);
      expect(GetCurrentUser()).toBeUndefined();
    });
  });

  describe("GetCurrentRoles", () => {
    it("returns parsed roles when token has roles", () => {
      vi.mocked(tokenService.GetToken).mockReturnValue(mockToken);
      const roles = GetCurrentRoles();
      expect(roles).toBeDefined();
      expect(roles).toHaveLength(2);
      expect(roles![0].name).toBe("Admin");
      expect(roles![1].name).toBe("Operator");
    });

    it("returns undefined when token is null", () => {
      vi.mocked(tokenService.GetToken).mockReturnValue(null);
      expect(GetCurrentRoles()).toBeUndefined();
    });

    it("returns undefined when token has no roles", () => {
      const tokenNoRoles = createMockJWT({ username: "test" });
      vi.mocked(tokenService.GetToken).mockReturnValue(tokenNoRoles);
      expect(GetCurrentRoles()).toBeUndefined();
    });
  });

  describe("GetUsers", () => {
    it("fetches and returns users on success", async () => {
      const mockUsers = [
        { id: "1", username: "admin" },
        { id: "2", username: "operator" },
      ];
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => mockUsers,
      });

      const result = await GetUsers();
      expect(result).toEqual(mockUsers);
      expect(fetch).toHaveBeenCalledWith("/api/v1/users/", {
        headers: expect.any(Headers),
        method: "GET",
      });
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: () => ({}),
      });

      await expect(GetUsers()).rejects.toThrow("HTTP error: Status 403");
    });
  });

  describe("DeleteUser", () => {
    it("sends DELETE request on success", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({}),
      });

      await DeleteUser("testuser");

      expect(fetch).toHaveBeenCalledWith("/api/v1/users/testuser", {
        headers: expect.any(Headers),
        method: "DELETE",
      });
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: () => ({}),
      });

      await expect(DeleteUser("testuser")).rejects.toThrow(
        "HTTP error: Status 404",
      );
    });
  });

  describe("CreateUser", () => {
    it("sends POST request with username and password", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({}),
      });

      await CreateUser("newuser", "password");

      const callArgs = (globalThis.fetch as any).mock.calls[0];
      expect(callArgs[0]).toBe("/api/v1/users/");
      expect(callArgs[1].method).toBe("POST");
      expect(callArgs[1].body).toBe(
        JSON.stringify({ username: "newuser", password: "password" }),
      );
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => ({}),
      });

      await expect(CreateUser("newuser", "pass")).rejects.toThrow(
        "HTTP error: Status 400",
      );
    });
  });

  describe("UserUpdatePassword", () => {
    it("sends POST request with current and new password", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({}),
      });

      await UserUpdatePassword("newpass", "currentpass");

      const callArgs = (globalThis.fetch as any).mock.calls[0];
      expect(callArgs[0]).toBe("/api/v1/password/change/");
      expect(callArgs[1].method).toBe("POST");
      expect(callArgs[1].body).toBe(
        JSON.stringify({
          current_password: "currentpass",
          new_password: "newpass",
        }),
      );
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 403,
        json: () => ({}),
      });

      await expect(UserUpdatePassword("new", "current")).rejects.toThrow(
        "HTTP error: Status 403",
      );
    });
  });
});
