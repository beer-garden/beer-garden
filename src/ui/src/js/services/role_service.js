import _ from "lodash";

roleService.$inject = ["$http"];

/**
 * roleService - Service for interacting with the role API.
 * @param  {$http} $http Angular's $http Object.
 * @return {Object}      Service for interacting with the role API.
 */
export default function roleService($http) {
  let service = {
    getRole: (roleId) => {
      return $http.get("api/v1/roles/" + roleId);
    },
    deleteRole: (roleId) => {
      return $http.delete("api/v1/roles/" + roleId);
    },
    updateRole: (roleId, operations) => {
      return $http.patch("api/v1/roles/" + roleId, { operations: operations });
    },
    getRoles: () => {
      return $http.get("api/v1/roles/");
    },
    createRole: (newRole) => {
      return $http.post("api/v1/roles/", newRole);
    },
  };

  /**
   * coalescePermissions - Determine effective permissions
   * @param  {Array} roleList Array of roles
   * @return {Array}          Array [set(all roles), set(all permissions)]
   */
  function coalescePermissions(roleList) {
    if (!roleList) {
      return [[], []];
    }

    let aggregateRoles = [];
    let aggregatePerms = [];

    for (let role of roleList) {
      aggregateRoles.push(role.name);
      aggregatePerms = _.union(aggregatePerms, role.permissions);

      let recursed = coalescePermissions(role.roles);
      aggregateRoles = _.union(aggregateRoles, recursed[0]);
      aggregatePerms = _.union(aggregatePerms, recursed[1]);
    }

    return [aggregateRoles, aggregatePerms];
  }

  _.assign(service, {
    addPermissions: (roleId, permissions) => {
      return service.updateRole(
        roleId,
        _.map(permissions, (value) => {
          return { operation: "add", path: "/permissions", value: value };
        })
      );
    },
    removePermissions: (roleId, permissions) => {
      return service.updateRole(
        roleId,
        _.map(permissions, (value) => {
          return { operation: "remove", path: "/permissions", value: value };
        })
      );
    },
    setPermissions: (roleId, permissions) => {
      return service.updateRole(roleId, [
        { operation: "set", path: "/permissions", value: permissions },
      ]);
    },
    addRoles: (roleId, roles) => {
      return service.updateRole(
        roleId,
        _.map(roles, (value) => {
          return { operation: "add", path: "/roles", value: value };
        })
      );
    },
    removeRoles: (roleId, roles) => {
      return service.updateRole(
        roleId,
        _.map(roles, (value) => {
          return { operation: "remove", path: "/roles", value: value };
        })
      );
    },
    setRoles: (roleId, roles) => {
      return service.updateRole(roleId, [
        { operation: "set", path: "/roles", value: roles },
      ]);
    },
    coalescePermissions: coalescePermissions,
  });

  return service;
}
