import { describe, expect, it } from "vitest";

import { Role } from "../models/brewtils-types";
import { PermissionCheck } from "../models/models";
import { CheckUserHasRoles } from "./permission_service";

describe("PermissionTesting", () => {
  it.each([
    { access: "READ_ONLY", permissionCheck: "GARDEN_ADMIN", expected: false },
    { access: "OPERATOR", permissionCheck: "GARDEN_ADMIN", expected: false },
    {
      access: "PLUGIN_ADMIN",
      permissionCheck: "GARDEN_ADMIN",
      expected: false,
    },
    { access: "GARDEN_ADMIN", permissionCheck: "GARDEN_ADMIN", expected: true },
    { access: "READ_ONLY", permissionCheck: "PLUGIN_ADMIN", expected: false },
    { access: "OPERATOR", permissionCheck: "PLUGIN_ADMIN", expected: false },
    { access: "PLUGIN_ADMIN", permissionCheck: "PLUGIN_ADMIN", expected: true },
    { access: "GARDEN_ADMIN", permissionCheck: "PLUGIN_ADMIN", expected: true },
    { access: "READ_ONLY", permissionCheck: "OPERATOR", expected: false },
    { access: "OPERATOR", permissionCheck: "OPERATOR", expected: true },
    { access: "PLUGIN_ADMIN", permissionCheck: "OPERATOR", expected: true },
    { access: "GARDEN_ADMIN", permissionCheck: "OPERATOR", expected: true },
    { access: "READ_ONLY", permissionCheck: "READ_ONLY", expected: true },
    { access: "OPERATOR", permissionCheck: "READ_ONLY", expected: true },
    { access: "PLUGIN_ADMIN", permissionCheck: "READ_ONLY", expected: true },
    { access: "GARDEN_ADMIN", permissionCheck: "READ_ONLY", expected: true },
  ])(
    `Role Access $access Permission $permissionCheck -> $expected`,
    ({ access, permissionCheck, expected }) => {
      const roles = [{ permission: access } as Role];
      expect(CheckUserHasRoles(roles, permissionCheck, {})).toBe(expected);
    },
  );

  it.each([
    { checkValue: "passed", expected: true },
    { checkValue: "failed", expected: false },
  ])(
    `Garden Scope Test Access $checkValue -> $expected`,
    ({ checkValue, expected }) => {
      const roles = [
        { permission: "READ_ONLY", scope_gardens: [checkValue] } as Role,
      ];
      expect(
        CheckUserHasRoles(roles, "READ_ONLY", {
          gardenName: "passed",
        } as PermissionCheck),
      ).toBe(expected);
    },
  );

  it.each([
    { checkValue: "passed", expected: true },
    { checkValue: "failed", expected: false },
  ])(
    `Namespace Scope Test Access $checkValue -> $expected`,
    ({ checkValue, expected }) => {
      const roles = [
        { permission: "READ_ONLY", scope_namespaces: [checkValue] } as Role,
      ];
      expect(
        CheckUserHasRoles(roles, "READ_ONLY", {
          namespace: "passed",
        } as PermissionCheck),
      ).toBe(expected);
    },
  );

  it.each([
    { checkValue: "passed", expected: true },
    { checkValue: "failed", expected: false },
  ])(
    `System Scope Test Access $checkValue -> $expected`,
    ({ checkValue, expected }) => {
      const roles = [
        { permission: "READ_ONLY", scope_systems: [checkValue] } as Role,
      ];
      expect(
        CheckUserHasRoles(roles, "READ_ONLY", {
          systemName: "passed",
        } as PermissionCheck),
      ).toBe(expected);
    },
  );

  it.each([
    { checkValue: "passed", expected: true },
    { checkValue: "failed", expected: false },
  ])(
    `System Version Scope Test Access $checkValue -> $expected`,
    ({ checkValue, expected }) => {
      const roles = [
        { permission: "READ_ONLY", scope_versions: [checkValue] } as Role,
      ];
      expect(
        CheckUserHasRoles(roles, "READ_ONLY", {
          systemVersion: "passed",
        } as PermissionCheck),
      ).toBe(expected);
    },
  );

  it.each([
    { checkValue: "passed", expected: true },
    { checkValue: "failed", expected: false },
  ])(
    `Instance Scope Test Access $checkValue -> $expected`,
    ({ checkValue, expected }) => {
      const roles = [
        { permission: "READ_ONLY", scope_instances: [checkValue] } as Role,
      ];
      expect(
        CheckUserHasRoles(roles, "READ_ONLY", {
          instanceName: "passed",
        } as PermissionCheck),
      ).toBe(expected);
    },
  );

  it.each([
    { checkValue: "passed", expected: true },
    { checkValue: "failed", expected: false },
  ])(
    `System Scope Test Access $checkValue -> $expected`,
    ({ checkValue, expected }) => {
      const roles = [
        { permission: "READ_ONLY", scope_commands: [checkValue] } as Role,
      ];
      expect(
        CheckUserHasRoles(roles, "READ_ONLY", {
          commandName: "passed",
        } as PermissionCheck),
      ).toBe(expected);
    },
  );

  it.each([
    { permissionCheck: { global: true } as PermissionCheck, expected: true },
    {
      permissionCheck: {
        global: true,
        gardenName: "failed",
      } as PermissionCheck,
      expected: false,
    },
    {
      permissionCheck: { global: true, namespace: "failed" } as PermissionCheck,
      expected: false,
    },
    {
      permissionCheck: {
        global: true,
        systemName: "failed",
      } as PermissionCheck,
      expected: false,
    },
    {
      permissionCheck: {
        global: true,
        systemVersion: "failed",
      } as PermissionCheck,
      expected: false,
    },
    {
      permissionCheck: {
        global: true,
        instanceName: "failed",
      } as PermissionCheck,
      expected: false,
    },
    {
      permissionCheck: {
        global: true,
        commandName: "failed",
      } as PermissionCheck,
      expected: false,
    },
  ])(
    `Global Test Check $permissionCheck -> $expected`,
    ({ permissionCheck, expected }) => {
      const roles = [{ permission: "READ_ONLY" } as Role];
      expect(CheckUserHasRoles(roles, "READ_ONLY", permissionCheck)).toBe(
        expected,
      );
    },
  );

  it.each([
    { roleCheck: { permission: "READ_ONLY" } as Role, expected: true },
    {
      roleCheck: { permission: "READ_ONLY", scope_gardens: ["failed"] } as Role,
      expected: false,
    },
    {
      roleCheck: {
        permission: "READ_ONLY",
        scope_namespaces: ["failed"],
      } as Role,
      expected: false,
    },
    {
      roleCheck: { permission: "READ_ONLY", scope_systems: ["failed"] } as Role,
      expected: false,
    },
    {
      roleCheck: {
        permission: "READ_ONLY",
        scope_versions: ["failed"],
      } as Role,
      expected: false,
    },
    {
      roleCheck: {
        permission: "READ_ONLY",
        scope_instances: ["failed"],
      } as Role,
      expected: false,
    },
    {
      roleCheck: {
        permission: "READ_ONLY",
        scope_commands: ["failed"],
      } as Role,
      expected: false,
    },
  ])(`Global Test Role $roleCheck -> $expected`, ({ roleCheck, expected }) => {
    const roles = [roleCheck];
    expect(
      CheckUserHasRoles(roles, "READ_ONLY", {
        global: true,
      } as PermissionCheck),
    ).toBe(expected);
  });

  function getAllCombinations(arr: Array<string>) {
    const combinations = [] as Array<Array<string>>;

    function backtrack(
      currentCombination: Array<string>,
      remainingElements: Array<string>,
    ) {
      // When no elements are left, if the current combination is not empty, add it to results
      if (remainingElements.length === 0) {
        if (currentCombination.length > 0) {
          combinations.push(currentCombination);
        }
        return;
      }

      // Case 1: Include the current element
      backtrack(
        [...currentCombination, remainingElements[0]],
        remainingElements.slice(1),
      );

      // Case 2: Exclude the current element
      backtrack(currentCombination, remainingElements.slice(1));
    }

    // Initial call with an empty combination and the full array
    backtrack([], arr);

    const results = [] as Array<{ scopes: Array<string>; role: Role }>;

    for (const combo of combinations) {
      const role = { permission: "READ_ONLY" } as any;
      for (const roleScope of combo) {
        role[roleScope] = ["passed"];
      }
      results.push({ scopes: combo, role: role as Role });
    }

    return results;
  }

  it.each(
    getAllCombinations([
      "scope_gardens",
      "scope_namespaces",
      "scope_systems",
      "scope_versions",
      "scope_instances",
      "scope_commands",
    ]),
  )(`Wildcard Role Support $scopes`, ({ role }) => {
    const roles = [role];
    expect(
      CheckUserHasRoles(roles, "READ_ONLY", {
        gardenName: "passed",
        namespace: "passed",
        systemName: "passed",
        systemVersion: "passed",
        instanceName: "passed",
        commandName: "passed",
      } as PermissionCheck),
    ).toBe(true);
  });
});
