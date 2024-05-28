permissionService.$inject = ['$rootScope'];

/**
 * permissionService - Used for filtering logic based on User roles
 * @param  {$rootScope} $rootScope Angular's $rootScope object
 * @return {Object}                For use by a controller.
 */
export default function permissionService($rootScope) {
    const service = {
        hasPermission: (permission, global = false, garden_name = null, namespace = null, system_name = null, system_version = null, command_name = null, instance_name = null) => {
            if (!$rootScope.config.authEnabled) return true;
            if (_.isUndefined($rootScope.user)) return false;

            let permissions = service.get_permissions(permission);

            if ($rootScope.user.local_roles !== undefined) {
                for (let i = 0; i < $rootScope.user.local_roles.length; i++) {
                    if (permissions.includes($rootScope.user.local_roles[i].permission)) {
                        if (service.checkRole($rootScope.user.local_roles[i], global = global, garden_name = garden_name, namespace = namespace, system_name = system_name, instance_name = instance_name, system_version = system_version, command_name = command_name)) {
                            return true;
                        }
                    }
                }
            }

            if ($rootScope.user.remote_roles !== undefined) {
                for (let i = 0; i < $rootScope.user.remote_roles.length; i++) {
                    if (permissions.includes($rootScope.user.remote_roles[i].permission)) {
                        if (service.checkRole($rootScope.user.remote_roles[i], global = global, garden_name = garden_name, namespace = namespace, system_name = system_name, instance_name = instance_name, system_version = system_version, command_name = command_name)) {
                            return true;
                        }
                    }
                }
            }

            return false;
        },
        get_permissions: (permission) => {
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
        },
        checkRole: (role, global = false, garden_name = null, namespace = null, system_name = null, instance_name = null, system_version = null, command_name = null) => {
            // Global checks are to ensure all fields not provided are empty
            
            if (garden_name !== undefined && garden_name != null && role.scope_gardens.length > 0 && !role.scope_gardens.includes(garden_name)) {
                return false;
            } else if (global && garden_name !== undefined && garden_name != null && role.scope_gardens.length > 0) {
                return false
            }

            if (namespace !== undefined && namespace != null && role.scope_namespaces.length > 0 && !role.scope_namespaces.includes(namespace)) {
                return false;
            } else if (global && namespace !== undefined && namespace != null && role.scope_namespaces.length > 0) {
                return false
            }

            if (system_name !== undefined && system_name != null && role.scope_systems.length > 0 && !role.scope_systems.includes(system_name)) {
                return false;
            } else if (global && system_name !== undefined && system_name != null && role.scope_systems.length > 0) {
                return false
            }

            if (instance_name !== undefined && instance_name != null && role.scope_instances.length > 0 && !role.scope_instances.includes(instance_name)) {
                return false;
            } else if (global && instance_name !== undefined && instance_name != null && role.scope_instances.length > 0 ) {
                return false
            }

            if (system_version !== undefined && system_version != null && role.scope_versions.length > 0 && !role.scope_versions.includes(system_version)) {
                return false;
            } else if (global && system_version !== undefined && system_version != null && role.scope_versions.length > 0) {
                return false
            }

            if (command_name !== undefined && command_name != null && role.scope_commands.length > 0 && !role.scope_commands.includes(command_name)) {
                return false;
            } else if (global && command_name !== undefined && command_name != null && role.scope_commands.length > 0) {
                return false
            }

            return true;
        },
        findGardenScope: (garden = null, namespace = null, system_name = null, system_version = null) => {
            if (garden === undefined || garden == null) {
                garden = $rootScope.garden;
            }

            if (garden.systems !== undefined || garden.systems != null) {
                for (let i = 0; i < garden.systems.length; i++) {
                    if (garden.systems[i].namespace != namespace) {
                        continue;
                    }
                    if (garden.systems[i].name != system_name) {
                        continue;
                    }

                    if (garden.systems[i].version != system_version) {
                        continue;
                    }

                    return true;
                }
            }

            if (garden.children !== undefined || garden.children != null) {
                for (let i = 0; i < garden.children.length; i++) {
                    garden_name = service.findGardenScope(garden = garden.children[i], namespace = namespace, system_name = system_name, instance_name = instance_name, system_version = system_version)
                    if (garden_name !== undefined || garden_name != null) {
                        return garden_name;
                    }
                }
            }

            return null;
        },
    };

    return service;
}