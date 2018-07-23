import _ from 'lodash';

tokenService.$inject = [
  '$rootScope',
  '$http',
  'localStorageService',
  'UserService',
];

/**
 * tokenService - Service for interacting with the token API.
 * @param  {$rootScope} $rootScope Angular's $rootScope Object.
 * @param  {$http} $http Angular's $http Object.
 * @param  {localStorageService} localStorageService Storage service
 * @param  {UserService} UserService       Service for User information.
 * @return {Object}      Service for interacting with the token API.
 */
export default function tokenService(
    $rootScope,
    $http,
    localStorageService,
    UserService) {
  let service = {
    doLogin: (username, password) => {
      return $http.post('/api/v1/tokens', {
        username: username,
        password: password,
      });
    },
    handleToken: (token) => {
      localStorageService.set('token', token);
      $http.defaults.headers.common.Authorization = 'Bearer ' + token;

      UserService.loadUser(token).then(response => {
        $rootScope.user = response.data;
        $rootScope.changeTheme($rootScope.user.preferences.theme || 'default');
      });
    },
    handleRefresh: (refreshToken) => {
      localStorageService.set('refresh', refreshToken);
    },
  };

  return service;
};
