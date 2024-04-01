filterService.$inject = ['$rootScope'];

/**
 * filterService - Used for filtering logic based on User roles
 * @param  {$rootScope} $rootScope Angular's $rootScope object
 * @return {Object}                For use by a controller.
 */
export default function permissionService($rootScope) {
    return {
        hasPermission: (permission, garden_name = null, namespace = null, system_name = null, instance_name = null, system_version = null, command_name = null) => {
            if (!$rootScope.config.authEnabled) return true;
            if (_.isUndefined($rootScope.user)) return false;

            if ($rootScope.user.local_roles !== undefined) {
                for (let i = 0; i < $rootScope.user.local_roles.length; i++) {
                    if ($rootScope.user.local_roles[i].permission == permission) {
                        if (checkRole($rootScope.user.local_roles[i], garden_name = garden_name, namespace = namespace, system_name = system_name, instance_name = instance_name, system_version = system_version, command_name = command_name)) {
                            return true;
                        }
                    }
                }
            }

            if ($rootScope.user.remote_roles !== undefined) {
                for (let i = 0; i < $rootScope.user.remote_roles.length; i++) {
                    if ($rootScope.user.remote_roles[i].permission == permission) {
                        if (checkRole($rootScope.user.remote_roles[i], garden_name = garden_name, namespace = namespace, system_name = system_name, instance_name = instance_name, system_version = system_version, command_name = command_name)) {
                            return true;
                        }
                    }
                }
            }

            return false;
        },
        checkRole: (role, garden_name = null, namespace = null, system_name = null, instance_name = null, system_version = null, command_name = null) => {
            if (garden_name !== undefined && garden_name != null && role.scope_gardens.length > 0 && !role.scope_gardens.includes(garden_name)) {
                return false;
            }
            if (namespace !== undefined && namespace != null && role.scope_namespaces.length > 0 && !role.scope_namespaces.includes(namespace)) {
                return false;
            }
            if (system_name !== undefined && system_name != null && role.scope_systems.length > 0 && !role.scope_systems.includes(system_name)) {
                return false;
            }
            if (instance_name !== undefined && instance_name != null && role.scope_instances.length > 0 && !role.scope_instances.includes(instance_name)) {
                return false;
            }
            if (system_version !== undefined && system_version != null && role.scope_versions.length > 0 && !role.scope_versions.includes(system_version)) {
                return false;
            }
            if (command_name !== undefined && command_name != null && role.scope_commands.length > 0 && !role.scope_commands.includes(command_name)) {
                return false;
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
                    garden_name = findGardenScope(garden = garden.children[i], namespace = namespace, system_name = system_name, instance_name = instance_name, system_version = system_version)
                    if (garden_name !== undefined || garden_name != null) {
                        return garden_name;
                    }
                }
            }

            return null;
        },
    };
}