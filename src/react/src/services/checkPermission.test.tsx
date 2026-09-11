import { beforeEach, describe, expect, test, vi } from "vitest";

import { Config, PermissionCheck } from "../models/models";
import { checkPermission } from "./permission_service";
import { GetCurrentRoles } from "./user_service";

vi.mock("./user_service");

describe("checkPermission", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const makeConfig = (authEnabled: boolean): Config =>
    ({ auth_enabled: authEnabled }) as Config;

  test("returns true when auth is disabled (auth_enabled is false)", () => {
    const config = makeConfig(false);
    expect(
      checkPermission(config, "GARDEN_ADMIN", {
        global: true,
      } as PermissionCheck),
    ).toBe(true);
  });

  test("returns true when auth_enabled is undefined", () => {
    const config = {} as Config;
    expect(
      checkPermission(config, "READ_ONLY", { global: true } as PermissionCheck),
    ).toBe(true);
  });

  test("returns true when user has required role and auth is enabled", () => {
    const config = makeConfig(true);
    vi.mocked(GetCurrentRoles).mockReturnValue([
      { permission: "GARDEN_ADMIN" } as any,
    ]);

    expect(
      checkPermission(config, "GARDEN_ADMIN", {
        global: true,
      } as PermissionCheck),
    ).toBe(true);
  });

  test("returns false when user lacks required role and auth is enabled", () => {
    const config = makeConfig(true);
    vi.mocked(GetCurrentRoles).mockReturnValue([
      { permission: "READ_ONLY" } as any,
    ]);

    expect(
      checkPermission(config, "GARDEN_ADMIN", {
        global: true,
      } as PermissionCheck),
    ).toBe(false);
  });

  test("returns false when no roles are stored", () => {
    const config = makeConfig(true);
    vi.mocked(GetCurrentRoles).mockReturnValue(undefined);

    expect(
      checkPermission(config, "READ_ONLY", { global: true } as PermissionCheck),
    ).toBe(false);
  });

  test("returns false when stored roles is empty array", () => {
    const config = makeConfig(true);
    vi.mocked(GetCurrentRoles).mockReturnValue([]);

    expect(
      checkPermission(config, "READ_ONLY", { global: true } as PermissionCheck),
    ).toBe(false);
  });
});

describe("GetPermissions", () => {
  // GetPermissions is not exported, so we test it indirectly through CheckUserHasRoles
  // but we can still verify the permission hierarchy via checkPermission

  test("READ_ONLY access is granted for GARDEN_ADMIN role", () => {
    const config = makeConfig(true);
    vi.mocked(GetCurrentRoles).mockReturnValue([
      { permission: "GARDEN_ADMIN" } as any,
    ]);

    expect(
      checkPermission(config, "READ_ONLY", { global: true } as PermissionCheck),
    ).toBe(true);
  });

  test("PLUGIN_ADMIN access is granted for GARDEN_ADMIN role", () => {
    const config = makeConfig(true);
    vi.mocked(GetCurrentRoles).mockReturnValue([
      { permission: "GARDEN_ADMIN" } as any,
    ]);

    expect(
      checkPermission(config, "PLUGIN_ADMIN", {
        global: true,
      } as PermissionCheck),
    ).toBe(true);
  });

  test("GARDEN_ADMIN access is NOT granted for PLUGIN_ADMIN role", () => {
    const config = makeConfig(true);
    vi.mocked(GetCurrentRoles).mockReturnValue([
      { permission: "PLUGIN_ADMIN" } as any,
    ]);

    expect(
      checkPermission(config, "GARDEN_ADMIN", {
        global: true,
      } as PermissionCheck),
    ).toBe(false);
  });

  test("GARDEN_ADMIN access is NOT granted for READ_ONLY role", () => {
    const config = makeConfig(true);
    vi.mocked(GetCurrentRoles).mockReturnValue([
      { permission: "READ_ONLY" } as any,
    ]);

    expect(
      checkPermission(config, "GARDEN_ADMIN", {
        global: true,
      } as PermissionCheck),
    ).toBe(false);
  });

  test("OPERATOR access is granted for OPERATOR role", () => {
    const config = makeConfig(true);
    vi.mocked(GetCurrentRoles).mockReturnValue([
      { permission: "OPERATOR" } as any,
    ]);

    expect(
      checkPermission(config, "OPERATOR", { global: true } as PermissionCheck),
    ).toBe(true);
  });

  test("unknown permission returns false", () => {
    const config = makeConfig(true);
    vi.mocked(GetCurrentRoles).mockReturnValue([
      { permission: "READ_ONLY" } as any,
    ]);

    expect(
      checkPermission(
        config,
        "SUPER_ADMIN" as any,
        { global: true } as PermissionCheck,
      ),
    ).toBe(false);
  });
});

function makeConfig(authEnabled: boolean): Config {
  return { auth_enabled: authEnabled } as Config;
}
