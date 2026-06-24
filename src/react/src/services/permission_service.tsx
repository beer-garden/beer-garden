import { Role } from "../models/brewtils-types";
import { Config, PermissionCheck } from "../models/models";
import { GetCurrentRoles } from "../services/user_service";

const GetPermissions = (permission: string): Array<string> => {
  switch (permission) {
    case "READ_ONLY":
      return ["READ_ONLY", "OPERATOR", "PLUGIN_ADMIN", "GARDEN_ADMIN"];
    case "OPERATOR":
      return ["OPERATOR", "PLUGIN_ADMIN", "GARDEN_ADMIN"];
    case "PLUGIN_ADMIN":
      return ["PLUGIN_ADMIN", "GARDEN_ADMIN"];
    case "GARDEN_ADMIN":
      return ["GARDEN_ADMIN"];
    default:
      return [];
  }
};

const CheckRole = (
  role: Role,
  permission: string,
  check: PermissionCheck,
): boolean => {
  if (
    role.permission === undefined ||
    role.permission === null ||
    !GetPermissions(permission).includes(role.permission)
  ) {
    return false;
  }

  if (check.global && check.global === true) {
    if (
      check.gardenName !== undefined ||
      (role.scope_gardens && role.scope_gardens?.length > 0)
    ) {
      return false;
    }
    if (
      check.namespace !== undefined ||
      (role.scope_namespaces && role.scope_namespaces?.length > 0)
    ) {
      return false;
    }
    if (
      check.systemName !== undefined ||
      (role.scope_systems && role.scope_systems?.length > 0)
    ) {
      return false;
    }
    if (
      check.systemVersion !== undefined ||
      (role.scope_versions && role.scope_versions?.length > 0)
    ) {
      return false;
    }
    if (
      check.instanceName !== undefined ||
      (role.scope_instances && role.scope_instances?.length > 0)
    ) {
      return false;
    }
    if (
      check.commandName !== undefined ||
      (role.scope_commands && role.scope_commands?.length > 0)
    ) {
      return false;
    }
  }

  const checkAccess = (
    target: string | undefined,
    scopes: Array<string> | undefined,
  ) => {
    if (target === undefined) {
      return true;
    }
    if (scopes === undefined || scopes.length === 0) {
      return true;
    }
    return scopes.includes(target);
  };

  if (!checkAccess(check.gardenName, role.scope_gardens)) {
    return false;
  }

  if (!checkAccess(check.namespace, role.scope_namespaces)) {
    return false;
  }

  if (!checkAccess(check.systemName, role.scope_systems)) {
    return false;
  }

  if (!checkAccess(check.systemVersion, role.scope_versions)) {
    return false;
  }

  if (!checkAccess(check.instanceName, role.scope_instances)) {
    return false;
  }

  if (!checkAccess(check.commandName, role.scope_commands)) {
    return false;
  }

  return true;
};

export const CheckUserHasRoles = (
  roles: Array<Role>,
  permission: string,
  check: PermissionCheck,
): boolean => {
  if (roles?.some((role) => CheckRole(role, permission, check))) {
    return true;
  }

  return false;
};

export const checkPermission = (
  config: Config,
  permission: "READ_ONLY" | "OPERATOR" | "PLUGIN_ADMIN" | "GARDEN_ADMIN",
  check: PermissionCheck,
): boolean => {
  if (config?.auth_enabled === undefined || config?.auth_enabled === false) {
    return true;
  }

  const storedRoles = GetCurrentRoles();

  if (!storedRoles) {
    return false;
  }

  return CheckUserHasRoles(storedRoles, permission, check);
};
