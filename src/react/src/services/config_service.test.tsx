import { beforeEach, describe, expect, it, vi } from "vitest";

import { GetConfig } from "./config_service";
import * as utilService from "./util_service";

vi.mock("./util_service");

describe("config_service", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(utilService.GetBaseURL).mockReturnValue("");
  });

  describe("GetConfig", () => {
    it("fetches and returns config on success", async () => {
      const mockConfig = {
        application_name: "Test Garden",
        auth_enabled: true,
      };
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () => mockConfig,
      });

      const result = await GetConfig();

      expect(result).toEqual(mockConfig);
      expect(fetch).toHaveBeenCalledWith("/config");
    });

    it("throws on non-ok response", async () => {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => ({}),
      });

      await expect(GetConfig()).rejects.toThrow("HTTP error: Status 500");
    });

    it("rethrows network errors", async () => {
      globalThis.fetch = vi.fn().mockRejectedValue(new Error("Network error"));

      await expect(GetConfig()).rejects.toThrow("Network error");
    });
  });
});
