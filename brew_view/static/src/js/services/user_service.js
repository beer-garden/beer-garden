import _ from 'lodash';
import jwtDecode from 'jwt-decode';

userService.$inject = ['$http'];

/**
 * userService - Service for interacting with the user API.
 * @param  {$http} $http Angular's $http Object.
 * @return {Object}      Service for interacting with the user API.
 */
export default function userService($http) {
  let service = {
    getUser: (userId) => {
      return $http.get('api/v1/users/' + userId);
    },
    deleteUser: (userId) => {
      return $http.delete('api/v1/users/' + userId);
    },
    updateUser: (userId, operations) => {
      return $http.patch('api/v1/users/' + userId, {operations: operations});
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
  };

  _.assign(service, {
    addRoles: (userId, roles) => {
      return service.updateUser(userId, _.map(roles, value => {
        return {operation: 'add', path: '/roles', value: value};
      }));
    },
    removeRoles: (userId, roles) => {
      return service.updateUser(userId, _.map(roles, value => {
        return {operation: 'remove', path: '/roles', value: value};
      }));
    },
    setRoles: (userId, roles) => {
      return service.updateUser(userId, [
        {operation: 'set', path: '/roles', value: roles},
      ]);
    },

    loadUser: (token) => {
      let decoded = jwtDecode(token);
      let userId = decoded.sub;

      return service.getUser(userId);
    },
    setTheme: (userId, theme) => {
      return service.updateUser(userId, [
        {operation: 'set', path: '/preferences/theme', value: theme},
      ]);
    },
  });

  return service;
};
