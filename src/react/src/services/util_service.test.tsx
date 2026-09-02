import { describe, expect, it, test } from "vitest";

import { Garden, Instance, System } from "../models/brewtils-types.js";
import {
  CompareObjects,
  GenerateStatusCounts,
  getErrorCode,
  GetSeverity,
} from "./util_service.js";

test("Compare Equal Objects", () => {
  expect(CompareObjects({ a: 1, b: 2 }, { a: 1, b: 2 })).toBe(true);
});

test("Compare Different Objects", () => {
  expect(CompareObjects({ a: 1, b: 2 }, { a: 1, b: 3 })).toBe(false);
});

it.each([
  { status: "INITIALIZING" },
  { status: "RUNNING" },
  { status: "PAUSED" },
  { status: "STOPPED" },
  { status: "DEAD" },
  { status: "UNRESPONSIVE" },
  { status: "STARTING" },
  { status: "STOPPING" },
  { status: "UNKNOWN" },
  { status: "AWAITING_SYSTEM" },
  { status: "ERROR" },
])(`system map $status`, ({ status }) => {
  const gardenRef = { current: { name: "root" } as Garden };

  const associatedRunners = { current: [] };

  const selectedGarden = {
    name: "child",
    systems: [
      {
        instances: [{ status: status } as Instance],
        local: false,
        garden_name: "child",
      } as System,
    ],
  } as Garden;

  const systems = selectedGarden.systems;

  const statusMap = GenerateStatusCounts(
    gardenRef,
    associatedRunners,
    selectedGarden,
    systems,
  );

  expect(statusMap.get(status)).toBe(1);
});

// --- Additional CompareObjects tests ---
describe("CompareObjects edge cases", () => {
  test("same reference returns true", () => {
    const obj = { a: 1 };
    expect(CompareObjects(obj, obj)).toBe(true);
  });

  test("different types returns false", () => {
    expect(CompareObjects(1, "1")).toBe(false);
    expect(CompareObjects(null, "null")).toBe(false);
  });

  test("null vs object returns false", () => {
    expect(CompareObjects(null, {})).toBe(false);
    expect(CompareObjects({}, null)).toBe(false);
  });

  test("objects with different number of keys returns false", () => {
    expect(CompareObjects({ a: 1 }, { a: 1, b: 2 })).toBe(false);
  });

  test("arrays compared regardless of order", () => {
    expect(CompareObjects([1, 2, 3], [3, 2, 1])).toBe(true);
    expect(CompareObjects([1, 2, 3], [3, 2, 4])).toBe(false);
  });

  test("nested objects compared correctly", () => {
    expect(CompareObjects({ a: { b: 1 } }, { a: { b: 1 } })).toBe(true);
    expect(CompareObjects({ a: { b: 1 } }, { a: { b: 2 } })).toBe(false);
  });

  test("undefined is falsy for null checks", () => {
    expect(CompareObjects(undefined, undefined)).toBe(true);
  });
});

// --- GetSeverity tests ---
describe("GetSeverity", () => {
  it("returns 'success' for RUNNING, HEALTHY, PUBLISHING, RECEIVING, SUCCESS", () => {
    expect(GetSeverity("RUNNING")).toBe("success");
    expect(GetSeverity("HEALTHY")).toBe("success");
    expect(GetSeverity("PUBLISHING")).toBe("success");
    expect(GetSeverity("RECEIVING")).toBe("success");
    expect(GetSeverity("SUCCESS")).toBe("success");
  });

  it("returns 'info' for PAUSED, STOPPED", () => {
    expect(GetSeverity("PAUSED")).toBe("info");
    expect(GetSeverity("STOPPED")).toBe("info");
  });

  it("returns 'warning' for INITIALIZING, STARTING, STOPPING, AWAITING_SYSTEM, DISABLED", () => {
    expect(GetSeverity("INITIALIZING")).toBe("warning");
    expect(GetSeverity("STARTING")).toBe("warning");
    expect(GetSeverity("STOPPING")).toBe("warning");
    expect(GetSeverity("AWAITING_SYSTEM")).toBe("warning");
    expect(GetSeverity("DISABLED")).toBe("warning");
  });

  it("returns 'error' for DEAD, UNRESPONSIVE, UNKNOWN, ERROR, INVALID, CANCELED", () => {
    expect(GetSeverity("DEAD")).toBe("error");
    expect(GetSeverity("UNRESPONSIVE")).toBe("error");
    expect(GetSeverity("UNKNOWN")).toBe("error");
    expect(GetSeverity("ERROR")).toBe("error");
    expect(GetSeverity("INVALID")).toBe("error");
    expect(GetSeverity("CANCELED")).toBe("error");
  });

  it("returns 'error' for unknown statuses (default)", () => {
    expect(GetSeverity("SOME_NEW_STATUS")).toBe("error");
    expect(GetSeverity(undefined)).toBe("error");
    expect(GetSeverity("")).toBe("error");
  });

  it("is case-insensitive", () => {
    expect(GetSeverity("running")).toBe("success");
    expect(GetSeverity("Paused")).toBe("info");
    expect(GetSeverity("error")).toBe("error");
  });
});

// --- getErrorCode tests ---
describe("getErrorCode", () => {
  it("extracts HTTP status code from error message", () => {
    expect(getErrorCode("HTTP error: Status 404")).toBe(404);
    expect(getErrorCode("HTTP error: Status 500")).toBe(500);
    expect(getErrorCode("HTTP error: Status 401")).toBe(401);
  });

  it("returns undefined for messages without HTTP error", () => {
    expect(getErrorCode("Some other error")).toBeUndefined();
  });

  it("returns undefined for empty/undefined input", () => {
    expect(getErrorCode("")).toBeUndefined();
    expect(getErrorCode(undefined as any)).toBeUndefined();
  });
});

// --- GenerateStatusCounts edge cases ---
describe("GenerateStatusCounts edge cases", () => {
  it("returns all-zero counts when systems is undefined", () => {
    const gardenRef = { current: { name: "root" } as Garden };
    const associatedRunners = { current: [] };
    const garden = { name: "root" } as Garden;

    const statusMap = GenerateStatusCounts(
      gardenRef,
      associatedRunners,
      garden,
      undefined,
    );

    expect(statusMap.get("RUNNING")).toBe(0);
    expect(statusMap.get("DEAD")).toBe(0);
  });

  it("counts UNASSOCIATED_RUNNER when runners are not assigned to systems", () => {
    const gardenRef = {
      current: { name: "root", connection_type: "LOCAL" } as Garden,
    };
    const associatedRunners = {
      current: [{ id: "r1", dead: false } as any],
    };
    const garden = {
      name: "root",
      connection_type: "LOCAL",
      children: [],
    } as Garden;
    const systems = [] as System[];

    const statusMap = GenerateStatusCounts(
      gardenRef,
      associatedRunners,
      garden,
      systems,
    );

    expect(statusMap.get("UNASSOCIATED_RUNNER")).toBe(1);
  });

  it("does not count UNASSOCIATED_RUNNER when garden is not root", () => {
    const gardenRef = {
      current: { name: "root" } as Garden,
    };
    const associatedRunners = {
      current: [{ id: "r1", dead: false } as any],
    };
    const garden = { name: "child" } as Garden;
    const systems: System[] = [];

    const statusMap = GenerateStatusCounts(
      gardenRef,
      associatedRunners,
      garden,
      systems,
    );

    expect(statusMap.get("UNASSOCIATED_RUNNER")).toBe(0);
  });

  it("counts multiple instances across systems", () => {
    const gardenRef = { current: { name: "root" } as Garden };
    const associatedRunners = { current: [] };
    const garden = {
      name: "child",
      systems: [
        {
          instances: [
            { status: "RUNNING" },
            { status: "RUNNING" },
          ] as Instance[],
          local: false,
          garden_name: "child",
        } as System,
        {
          instances: [{ status: "DEAD" }] as Instance[],
          local: false,
          garden_name: "child",
        } as System,
      ],
    } as Garden;

    const systems = garden.systems;

    const statusMap = GenerateStatusCounts(
      gardenRef,
      associatedRunners,
      garden,
      systems,
    );

    expect(statusMap.get("RUNNING")).toBe(2);
    expect(statusMap.get("DEAD")).toBe(1);
  });
});
