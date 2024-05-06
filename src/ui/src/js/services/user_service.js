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
      return $http.patch('api/v1/users/' + userName, {
        operation: 'update',
        path: '',
        value: userData,
      });
    },
    updateUserRoles: (userName, userData) => {
      return $http.patch('api/v1/users/' + userName, {
        operation: 'update_roles',
        path: '',
        value: {'roles':userData.roles},
      });
    },
    updateUserAccounts: (userName, userData) => {
      return $http.patch('api/v1/users/' + userName, {
        operation: 'update_user_mappings',
        path: '',
        value: {'remote_user_mapping':userData.remote_user_mapping},
      });
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
    adminChangePassword: (userName, password) => {
      return $http.patch('api/v1/users/' + userName, {
        operation: 'update_user_password',
        path: '',
        value: {'password':password},
      });
    },
    changePassword: (currentPassword, newPassword) => {
      return $http.post('api/v1/password/change/', {
        current_password: currentPassword,
        new_password: newPassword,
      });
    }
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
