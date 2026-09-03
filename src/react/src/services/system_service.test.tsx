import { beforeEach, describe, expect, it } from "vitest";

import { Garden, System } from "../models/brewtils-types";
import {
  ClearSystemsCache,
  CompareVersions,
  DetermineLatestSystemVersion,
  ExtractSystemsFromGardens,
} from "./system_service";

describe("system_service pure functions", () => {
  describe("ClearSystemsCache", () => {
    beforeEach(() => {
      sessionStorage.clear();
    });

    it("removes systems from sessionStorage", () => {
      sessionStorage.setItem("systems", JSON.stringify([{ name: "test" }]));
      ClearSystemsCache();
      expect(sessionStorage.getItem("systems")).toBeNull();
    });

    it("does not throw when systems not in sessionStorage", () => {
      expect(() => ClearSystemsCache()).not.toThrow();
    });
  });

  describe("ExtractSystemsFromGardens", () => {
    it("extracts all systems from gardens", () => {
      const gardens: Garden[] = [
        {
          name: "garden1",
          systems: [
            { id: "s1", name: "sys1" } as System,
            { id: "s2", name: "sys2" } as System,
          ],
        } as Garden,
        {
          name: "garden2",
          systems: [{ id: "s3", name: "sys3" } as System],
        } as Garden,
      ];

      const result = ExtractSystemsFromGardens(gardens, []);

      expect(result).toHaveLength(3);
      expect(result.map((s) => s.id)).toEqual(["s1", "s2", "s3"]);
    });

    it("handles gardens without systems", () => {
      const gardens: Garden[] = [
        { name: "garden1" } as Garden,
        {
          name: "garden2",
          systems: [{ id: "s1" } as System],
        } as Garden,
      ];

      const result = ExtractSystemsFromGardens(gardens, []);
      expect(result).toHaveLength(1);
      expect(result[0].id).toBe("s1");
    });

    it("handles empty garden array", () => {
      const result = ExtractSystemsFromGardens([], []);
      expect(result).toEqual([]);
    });

    it("appends to existing systems array (mutates)", () => {
      const gardens: Garden[] = [
        {
          systems: [{ id: "s1" } as System],
        } as Garden,
      ];
      const existing: System[] = [{ id: "existing" } as System];

      const result = ExtractSystemsFromGardens(gardens, existing);

      expect(result).toHaveLength(2);
      expect(result[0].id).toBe("existing");
      expect(result[1].id).toBe("s1");
    });
  });

  describe("DetermineLatestSystemVersion", () => {
    it("filters by namespace and name", () => {
      const systems: System[] = [
        { id: "1", namespace: "ns1", name: "sys1", version: "1.0.0" } as System,
        { id: "2", namespace: "ns2", name: "sys1", version: "2.0.0" } as System,
        { id: "3", namespace: "ns1", name: "sys2", version: "3.0.0" } as System,
      ];

      const result = DetermineLatestSystemVersion(
        systems,
        "sys1",
        "ns1",
        undefined,
      );

      expect(result.id).toBe("1");
    });

    it("filters by version when specified", () => {
      const systems: System[] = [
        { id: "1", version: "1.0.0" } as System,
        { id: "2", version: "2.0.0" } as System,
        { id: "3", version: "3.0.0" } as System,
      ];

      const result = DetermineLatestSystemVersion(
        systems,
        undefined,
        undefined,
        "2.0.0",
      );
      expect(result.id).toBe("2");
    });

    it("returns latest version when version is 'latest'", () => {
      const systems: System[] = [
        { id: "1", version: "1.0.0" } as System,
        { id: "2", version: "2.0.0" } as System,
      ];

      const result = DetermineLatestSystemVersion(
        systems,
        undefined,
        undefined,
        "latest",
      );
      expect(result.id).toBe("2");
    });

    it("handles .dev versions", () => {
      const systems: System[] = [
        { id: "1", version: "1.0.0.dev1" } as System,
        { id: "2", version: "2.0.0" } as System,
      ];

      const result = DetermineLatestSystemVersion(
        systems,
        undefined,
        undefined,
        undefined,
      );
      expect(result.id).toBe("2");
    });

    it("returns first system when all have same version", () => {
      const systems: System[] = [
        { id: "1", version: "1.0.0" } as System,
        { id: "2", version: "1.0.0" } as System,
      ];

      const result = DetermineLatestSystemVersion(
        systems,
        undefined,
        undefined,
        undefined,
      );
      expect(result.id).toBe("1");
    });
  });

  describe("CompareVersions", () => {
    it("returns 1 when versionA > versionB", () => {
      expect(CompareVersions("2.0.0", "1.0.0")).toBe(1);
    });

    it("returns -1 when versionA < versionB", () => {
      expect(CompareVersions("1.0.0", "2.0.0")).toBe(-1);
    });

    it("handles .dev versions", () => {
      expect(CompareVersions("2.0.0", "1.0.0.dev1")).toBe(1);
    });

    it("returns -1 when versionA is invalid and versionB is invalid", () => {
      expect(CompareVersions("abc", "xyz")).toBe(-1);
    });

    it("returns 1 when versionA is valid and versionB is invalid", () => {
      expect(CompareVersions("1.0.0", "xyz")).toBe(1);
    });

    it("returns -1 when versionA is invalid and versionB is valid", () => {
      expect(CompareVersions("xyz", "1.0.0")).toBe(-1);
    });
  });
});
