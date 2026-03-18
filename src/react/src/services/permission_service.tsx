import { Role, User } from "../models/brewtils-types";
import { PermissionCheck } from "../models/models";
//context

const LOCAL_STORAGE_KEY_USER = "__permissionUser";
const LOCAL_STORAGE_KEY_AUTH_ENABLED = "__permissionAuthEnabled";

export const updateUser = (newUser: User | undefined) => {
  if (newUser === undefined) {
    localStorage.removeItem(LOCAL_STORAGE_KEY_USER);
  } else {
    localStorage.setItem(LOCAL_STORAGE_KEY_USER, JSON.stringify(newUser));
  }
};

export const setAuthEnabled = (authEnabled: boolean) => {
  localStorage.setItem(
    LOCAL_STORAGE_KEY_AUTH_ENABLED,
    authEnabled ? "true" : "false",
  );
};

// MOVE to User Service
const getUser = () => {
  return localStorage.getItem(LOCAL_STORAGE_KEY_USER)
    ? JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY_USER) ?? "")
    : undefined;
};

// Move somewhere else
const getAuthEnabled = () => {
  return (
    localStorage.getItem(LOCAL_STORAGE_KEY_AUTH_ENABLED) !== null &&
    localStorage.getItem(LOCAL_STORAGE_KEY_AUTH_ENABLED) === "true"
  );
};

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
      (role.scopeGardens && role.scopeGardens?.length > 0)
    ) {
      return false;
    }
    if (
      check.namespace !== undefined ||
      (role.scopeNamespaces && role.scopeNamespaces?.length > 0)
    ) {
      return false;
    }
    if (
      check.systemName !== undefined ||
      (role.scopeSystems && role.scopeSystems?.length > 0)
    ) {
      return false;
    }
    if (
      check.systemVersion !== undefined ||
      (role.scopeVersions && role.scopeVersions?.length > 0)
    ) {
      return false;
    }
    if (
      check.instanceName !== undefined ||
      (role.scopeInstances && role.scopeInstances?.length > 0)
    ) {
      return false;
    }
    if (
      check.commandName !== undefined ||
      (role.scopeCommands && role.scopeCommands?.length > 0)
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

  if (!checkAccess(check.gardenName, role.scopeGardens)) {
    return false;
  }

  if (!checkAccess(check.namespace, role.scopeNamespaces)) {
    return false;
  }

  if (!checkAccess(check.systemName, role.scopeSystems)) {
    return false;
  }

  if (!checkAccess(check.systemVersion, role.scopeVersions)) {
    return false;
  }

  if (!checkAccess(check.instanceName, role.scopeInstances)) {
    return false;
  }

  if (!checkAccess(check.commandName, role.scopeCommands)) {
    return false;
  }

  return true;
};

export const CheckUserHasRoles = (
  storedUser: User,
  permission: string,
  check: PermissionCheck,
): boolean => {
  if (
    storedUser.localRoles?.some((role) => CheckRole(role, permission, check))
  ) {
    return true;
  }

  if (
    storedUser.upstreamRoles?.some((role) => CheckRole(role, permission, check))
  ) {
    return true;
  }

  return false;
};

export const checkPermission = (
  permission: string,
  check: PermissionCheck,
): boolean => {
  if (!getAuthEnabled()) {
    return true;
  }

  const storedUser = getUser();

  if (!storedUser) {
    console.log("No user logged in");
    return false;
  }

  return CheckUserHasRoles(storedUser, permission, check);
};
