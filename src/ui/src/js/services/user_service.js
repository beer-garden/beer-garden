import _ from 'lodash';
import jwtDecode from 'jwt-decode';

userService.$inject = ['$http', 'GardenService', 'SystemService'];

/**
 * userService - Service for interacting with the user API.
 * @param  {$http} $http           Angular's $http Object.
 * @param  {Object} GardenService  Beer-Garden's garden service object.
 * @param  {Object} SystemService  Beer-Garden's system service object.
 * @return {Object}                Service for interacting with the user API.
 */
export default function userService($http, GardenService, SystemService) {
  const service = {
    getUser: (userName) => {
      return $http.get('api/v1/users/' + userName);
    },
    deleteUser: (userName) => {
      return $http.delete('api/v1/users/' + userName);
    },
    updateUser: (userName, userData) => {
      return $http.patch('api/v1/users/' + userName, userData);
    },
    getUsers: () => {
      return $http.get('api/v1/users/');
    },
    createUser: (userName, password) => {
      return $http.post('api/v1/users/', {
        username: userName,
        password: password,
      });
    },
    changePassword: (currentPassword, newPassword) => {
      return $http.post('api/v1/password/change/', {
        current_password: currentPassword,
        new_password: newPassword,
      });
    },
    hasPermission: (user, permission) => {
      // True if the user has the permission for any objects at all
      return (
        user.permissions.global_permissions.includes(permission) ||
        user.permissions.domain_permissions.hasOwnProperty(permission)
      );
    },
    hasGardenPermission: (user, permission, garden) => {
      if (user.permissions.global_permissions.includes(permission)) {
        return true;
      }

      if (user.permissions.domain_permissions.hasOwnProperty(permission)) {
        return user.permissions.domain_permissions[
            permission
        ].garden_ids.includes(garden.id);
      }

      return false;
    },
    hasSystemPermission: (user, permission, system) => {
      if (user.permissions.global_permissions.includes(permission)) {
        return true;
      }

      const garden = GardenService.findGarden(system.namespace);
      if (garden && service.hasGardenPermission(user, permission, garden)) {
        return true;
      }

      if (user.permissions.domain_permissions.hasOwnProperty(permission)) {
        return user.permissions.domain_permissions[
            permission
        ].system_ids.includes(system.id);
      }

      return false;
    },
    hasCommandPermission: (user, permission, command) => {
      const system = SystemService.findSystem(
          command.namespace,
          command.system,
          command.version,
      );

      return service.hasSystemPermission(user, permission, system);
    },
    hasJobPermission: (user, permission, job) => {
      const system = SystemService.findSystem(
          job.request_template.namespace,
          job.request_template.system,
          job.request_template.system_version,
      );

      return service.hasSystemPermission(user, permission, system);
    },
  };

  _.assign(service, {
    loadUser: (token) => {
      return service.getUser(token ? jwtDecode(token).username : 'anonymous');
    },
    setTheme: (userId, theme) => {
      return service.updateUser(userId, [
        {operation: 'set', path: '/preferences/theme', value: theme},
      ]);
    },
  });

  return service;
}
