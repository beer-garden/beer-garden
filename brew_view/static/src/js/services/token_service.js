
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
    doRefresh: (refreshToken) => {
      return $http.get('/api/v1/tokens/' + refreshToken);
    },
    clearRefresh: (refreshToken) => {
      // It's possible the refresh token was already removed from the database
      // We usually don't care if that's the case, so set a noop error handler
      return $http.delete('api/v1/tokens/' + refreshToken).catch(() => {});
    },
    handleToken: (token) => {
      localStorageService.set('token', token);
      $http.defaults.headers.common.Authorization = 'Bearer ' + token;
    },
    handleRefresh: (refreshToken) => {
      localStorageService.set('refresh', refreshToken);
    },
  };

  return service;
};
