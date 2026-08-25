import { beforeEach, describe, expect, it, vi } from "vitest";

import { Garden, Patch } from "../models/brewtils-types";
import { Config } from "../models/models";
import * as gardenService from "./garden_service";
import * as tokenService from "./token_service";
import * as utilService from "./util_service";

vi.mock("./token_service");
vi.mock("./util_service");

describe("garden_service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(utilService.GetBaseURL).mockReturnValue("");
    vi.mocked(tokenService.GetAuthHeaders).mockReturnValue(new Headers());
  });

  describe("GetGarden", () => {
    it("fetches a garden by name and returns data", async () => {
      const mockGarden: Garden = { id: "g1", name: "test_garden" } as Garden;
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => mockGarden,
      });

      const result = await gardenService.GetGarden("test_garden");

      expect(result).toEqual(mockGarden);
      expect(fetch).toHaveBeenCalledWith(
        "/api/v1/gardens/test_garden",
        expect.objectContaining({ headers: expect.any(Headers) }),
      );
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: () => ({}),
      });

      await expect(gardenService.GetGarden("missing")).rejects.toThrow(
        "HTTP error: Status 404",
      );
    });

    it("passes through custom headerData", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({}),
      });

      await gardenService.GetGarden("test", { "Target-Garden": "test" });

      const [, options] = (globalThis.fetch as any).mock.calls[0];
      expect(options.headers.get("Target-Garden")).toBe("test");
    });
  });

  describe("PatchGarden", () => {
    it("sends PATCH with patch object", async () => {
      const patch: Patch = { operation: "sync", path: "", value: "" };
      const mockGarden: Garden = { id: "g1", name: "test" } as Garden;
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => mockGarden,
      });

      const result = await gardenService.PatchGarden(patch, "test_garden");

      expect(result).toEqual(mockGarden);
      const [, options] = (globalThis.fetch as any).mock.calls[0];
      expect(options.method).toBe("PATCH");
      expect(options.body).toBe(JSON.stringify(patch));
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => ({}),
      });

      await expect(
        gardenService.PatchGarden(
          { operation: "sync", path: "", value: "" } as Patch,
        ),
      ).rejects.toThrow("HTTP error: Status 500");
    });
  });

  describe("DeleteGarden", () => {
    it("sends DELETE request", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({}),
      });

      await gardenService.DeleteGarden("test_garden");

      const [url, options] = (globalThis.fetch as any).mock.calls[0];
      expect(url).toBe("/api/v1/gardens/test_garden");
      expect(options.method).toBe("DELETE");
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: () => ({}),
      });

      await expect(gardenService.DeleteGarden("missing")).rejects.toThrow(
        "HTTP error: Status 404",
      );
    });
  });

  describe("GetRootGarden", () => {
    it("returns garden when config has garden_name", async () => {
      const mockGarden: Garden = { id: "g1", name: "root" } as Garden;
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => mockGarden,
      });

      const config: Config = { garden_name: "root" } as Config;
      const result = await gardenService.GetRootGarden(config);

      expect(result).toEqual(mockGarden);
      expect(fetch).toHaveBeenCalledWith(
        "/api/v1/gardens/root",
        expect.objectContaining({ headers: expect.any(Headers) }),
      );
    });

    it("throws when config has no garden_name", async () => {
      const config: Config = {} as Config;
      await expect(gardenService.GetRootGarden(config)).rejects.toThrow(
        "Root garden not defined in config",
      );
    });

    it("passes headerData through", async () => {
      const mockGarden: Garden = { id: "g1", name: "root" } as Garden;
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => mockGarden,
      });

      const config: Config = { garden_name: "root" } as Config;
      const headerData = { "X-Custom": "value" };
      const result = await gardenService.GetRootGarden(config, headerData);

      expect(result).toEqual(mockGarden);
      const [, options] = (globalThis.fetch as any).mock.calls[0];
      expect(options.headers.get("X-Custom")).toBe("value");
    });
  });

  describe("GetGardenList", () => {
    it("fetches and returns garden list", async () => {
      const mockGardens = [{ id: "1", name: "garden1" }] as Garden[];
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => mockGardens,
      });

      const result = await gardenService.GetGardenList();

      expect(result).toEqual(mockGardens);
      const [url, options] = (globalThis.fetch as any).mock.calls[0];
      expect(url).toBe("/api/v1/gardens/");
      // GetGardenList doesn't explicitly set method (defaults to GET)
      expect(options).toHaveProperty("headers");
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => ({}),
      });

      await expect(gardenService.GetGardenList()).rejects.toThrow(
        "HTTP error: Status 500",
      );
    });

    it("passes through custom headerData", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({}),
      });

      await gardenService.GetGardenList({ "X-Custom": "value" });

      const [, options] = (globalThis.fetch as any).mock.calls[0];
      expect(options.headers.get("X-Custom")).toBe("value");
    });
  });

  describe("SyncGarden", () => {
    it("calls PatchGarden with sync operation and garden name", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({ id: "1", name: "my_garden" } as Garden),
      });

      const result = await gardenService.SyncGarden("my_garden");

      expect(result).toEqual({ id: "1", name: "my_garden" } as Garden);
      const [, options] = (globalThis.fetch as any).mock.calls[0];
      expect(options.method).toBe("PATCH");
      expect(options.body).toBe(
        JSON.stringify({ operation: "sync", path: "", value: "" }),
      );
      expect(options.headers.get("Target-Garden")).toBe("my_garden");
    });

    it("calls PatchGarden without garden name", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({ id: "1" } as Garden),
      });

      const result = await gardenService.SyncGarden();

      expect(result).toEqual({ id: "1" } as Garden);
      const [url, options] = (globalThis.fetch as any).mock.calls[0];
      expect(url).toBe("/api/v1/gardens");
      expect(options.method).toBe("PATCH");
      expect(options.body).toBe(
        JSON.stringify({ operation: "sync", path: "", value: "" }),
      );
    });
  });

  describe("RescanGarden", () => {
    it("calls PatchGarden with rescan operation", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({ id: "1" } as Garden),
      });

      await gardenService.RescanGarden("my_garden");

      const [, options] = (globalThis.fetch as any).mock.calls[0];
      expect(options.method).toBe("PATCH");
      expect(options.body).toBe(
        JSON.stringify({ operation: "rescan", path: "", value: "" }),
      );
      expect(options.headers.get("Target-Garden")).toBe("my_garden");
    });
  });

  describe("SyncUsersGarden", () => {
    it("calls PatchGarden with sync_users operation", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({ id: "1" } as Garden),
      });

      await gardenService.SyncUsersGarden("my_garden");

      const [, options] = (globalThis.fetch as any).mock.calls[0];
      expect(options.method).toBe("PATCH");
      expect(options.body).toBe(
        JSON.stringify({ operation: "sync_users", path: "", value: "" }),
      );
      expect(options.headers.get("Target-Garden")).toBe("my_garden");
    });
  });

  describe("UpdateApiGarden", () => {
    it("calls PatchGarden with connection operation", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => ({ id: "1" } as Garden),
      });

      await gardenService.UpdateApiGarden("my_garden", "PUBLISHING", "HTTP", "Remote");

      const [url, options] = (globalThis.fetch as any).mock.calls[0];
      expect(url).toBe("/api/v1/gardens/my_garden");
      expect(options.method).toBe("PATCH");
      expect(options.body).toBe(
        JSON.stringify({
          operation: "connection",
          path: "",
          value: {
            status: "PUBLISHING",
            api: "HTTP",
            connection_type: "Remote",
          },
        }),
      );
    });
  });
});
