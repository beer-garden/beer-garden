
userService.$inject = ['$http'];

/**
 * userService - Service for interacting with the user API.
 * @param  {$http} $http Angular's $http Object.
 * @return {Object}      Service for interacting with the user API.
 */
export default function userService($http) {
  return {
    createUser: function(userName, password) {
      return $http.post('api/v1/users/', {
        username: userName,
        password: password,
      });
    },
    setTheme: function(userId, theme) {
      return $http.patch('api/v1/users/'+userId, {
        operations: [
          {operation: 'set', path: '/preferences/theme', value: theme}
        ]
      });
    },
  };
};
