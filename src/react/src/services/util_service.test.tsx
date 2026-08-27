import { expect, it, test } from "vitest";

import { Garden, Instance, System } from "../models/brewtils-types.js";
import {
  CompareObjects,
  GenerateStatusCounts,
  GetBaseURL,
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

it.each([
  { pathname: "/", prefix: "" },
  { pathname: "/dashboard", prefix: "" },
  { pathname: "/requests", prefix: "" },
  { pathname: "/jobs", prefix: "" },
  { pathname: "/about", prefix: "" },
  { pathname: "/roles", prefix: "" },
  { pathname: "/topics", prefix: "" },
  { pathname: "/users", prefix: "" },
  { pathname: "/swagger", prefix: "" },
  { pathname: "/request/id", prefix: "" },
  { pathname: "/pre/", prefix: "/pre" },
  { pathname: "/pre/dashboard", prefix: "/pre" },
  { pathname: "/pre/requests", prefix: "/pre" },
  { pathname: "/pre/jobs", prefix: "/pre" },
  { pathname: "/pre/about", prefix: "/pre" },
  { pathname: "/pre/roles", prefix: "/pre" },
  { pathname: "/pre/topics", prefix: "/pre" },
  { pathname: "/pre/users", prefix: "/pre" },
  { pathname: "/pre/swagger", prefix: "/pre" },
  { pathname: "/pre/request/id", prefix: "/pre" },
  { pathname: "/double/pre/", prefix: "/double/pre" },
  { pathname: "/double/pre/dashboard", prefix: "/double/pre" },
  { pathname: "/double/pre/requests", prefix: "/double/pre" },
  { pathname: "/double/pre/jobs", prefix: "/double/pre" },
  { pathname: "/double/pre/about", prefix: "/double/pre" },
  { pathname: "/double/pre/roles", prefix: "/double/pre" },
  { pathname: "/double/pre/topics", prefix: "/double/pre" },
  { pathname: "/double/pre/users", prefix: "/double/pre" },
  { pathname: "/double/pre/swagger", prefix: "/double/pre" },
  { pathname: "/double/pre/request/id", prefix: "/double/pre" },
])(`URL $pathname to Pre $prefix`, ({ pathname, prefix }) => {
  window.history.pushState({}, "Test Page", pathname);
  expect(window.location.pathname).toBe(pathname);

  expect(GetBaseURL()).toBe(prefix);
});
