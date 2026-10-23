import { expect, it, test } from "vitest";

import { Garden, Instance, System } from "../models/brewtils-types.js";
import { CompareObjects, GenerateStatusCounts } from "./util_service.js";

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
