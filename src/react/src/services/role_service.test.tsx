import { beforeEach, describe, expect, it, vi } from "vitest";

import { Role } from "../models/brewtils-types";
import {
  CreateRole,
  DeleteRole,
  EditRole,
  GetRole,
  GetRoles,
  Rescan,
} from "./role_service";
import * as tokenService from "./token_service";
import * as utilService from "./util_service";

vi.mock("./token_service");
vi.mock("./util_service");

describe("role_service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(utilService.GetBaseURL).mockReturnValue("");
    vi.mocked(tokenService.GetAuthHeaders).mockReturnValue(new Headers());
  });

  describe("GetRole", () => {
    it("fetches and returns a role by id", async () => {
      const mockRole: Role = {
        id: "r1",
        name: "admin",
        permission: "GARDEN_ADMIN",
      } as Role;
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => mockRole,
      });

      const result = await GetRole("r1");

      expect(result).toEqual(mockRole);
      const [url, options] = (globalThis.fetch as any).mock.calls[0];
      expect(url).toBe("/api/v1/roles/r1");
      expect(options.method).toBe("GET");
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: () => ({}),
      });

      await expect(GetRole("missing")).rejects.toThrow(
        "HTTP error: Status 404",
      );
    });
  });

  describe("DeleteRole", () => {
    it("sends DELETE request", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({}),
      });

      await DeleteRole("r1");

      const [url, options] = (globalThis.fetch as any).mock.calls[0];
      expect(url).toBe("/api/v1/roles/r1");
      expect(options.method).toBe("DELETE");
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => ({}),
      });

      await expect(DeleteRole("r1")).rejects.toThrow("HTTP error: Status 500");
    });
  });

  describe("EditRole", () => {
    it("sends PATCH with role data", async () => {
      const role: Role = {
        id: "r1",
        name: "updated",
        permission: "OPERATOR",
      } as Role;
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => role,
      });

      const result = await EditRole(role);

      expect(result).toEqual(role);
      const [, options] = (globalThis.fetch as any).mock.calls[0];
      expect(options.method).toBe("PATCH");
      const body = JSON.parse(options.body);
      expect(body.operations[0].operation).toBe("update_role");
      expect(body.operations[0].value).toEqual(role);
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => ({}),
      });

      await expect(EditRole({ id: "r1" } as Role)).rejects.toThrow(
        "HTTP error: Status 400",
      );
    });
  });

  describe("GetRoles", () => {
    it("fetches and returns role list", async () => {
      const mockRoles: Role[] = [
        { id: "r1", name: "admin", permission: "GARDEN_ADMIN" } as Role,
        { id: "r2", name: "operator", permission: "OPERATOR" } as Role,
      ];
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => mockRoles,
      });

      const result = await GetRoles();

      expect(result).toEqual(mockRoles);
      const [url, options] = (globalThis.fetch as any).mock.calls[0];
      expect(url).toBe("/api/v1/roles/");
      expect(options.method).toBe("GET");
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => ({}),
      });

      await expect(GetRoles()).rejects.toThrow("HTTP error: Status 500");
    });
  });

  describe("Rescan", () => {
    it("sends PATCH with rescan operation", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({}),
      });

      await Rescan();

      const [, options] = (globalThis.fetch as any).mock.calls[0];
      expect(options.method).toBe("PATCH");
      const body = JSON.parse(options.body);
      expect(body.operations[0].operation).toBe("rescan");
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => ({}),
      });

      await expect(Rescan()).rejects.toThrow("HTTP error: Status 500");
    });
  });

  describe("CreateRole", () => {
    it("sends POST with role data", async () => {
      const newRole: Role = {
        id: "new1",
        name: "newrole",
        permission: "READ_ONLY",
      } as Role;
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => newRole,
      });

      const result = await CreateRole(newRole);

      expect(result).toEqual(newRole);
      const [url, options] = (globalThis.fetch as any).mock.calls[0];
      expect(url).toBe("/api/v1/roles/");
      expect(options.method).toBe("POST");
      expect(options.body).toBe(JSON.stringify(newRole));
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        json: () => ({}),
      });

      await expect(CreateRole({ name: "bad" } as Role)).rejects.toThrow(
        "HTTP error: Status 400",
      );
    });
  });
});
