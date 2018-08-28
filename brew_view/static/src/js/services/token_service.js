import _ from 'lodash';

tokenService.$inject = [
  '$rootScope',
  '$http',
  'localStorageService',
];

/**
 * tokenService - Service for interacting with the token API.
 * @param  {Object} $rootScope          Angular's $rootScope Object.
 * @param  {Object} $http               Angular's $http Object.
 * @param  {Object} localStorageService Storage service
 * @return {Object}       Service for interacting with the token API.
 */
export default function tokenService(
    $rootScope,
    $http,
    localStorageService) {
  let service = {
    getToken: () => {
      return localStorageService.get('token');
    },
    handleToken: (token) => {
      localStorageService.set('token', token);
      $http.defaults.headers.common.Authorization = 'Bearer ' + token;
    },
    clearToken: () => {
      localStorageService.remove('token');
      $http.defaults.headers.common.Authorization = undefined;
    },
    getRefresh: () => {
      return localStorageService.get('refresh');
    },
    handleRefresh: (refreshToken) => {
      localStorageService.set('refresh', refreshToken);
    },
    clearRefresh: () => {
      let refreshToken = localStorageService.get('refresh');
      if (refreshToken) {
        // It's possible the refresh token was already removed from the database
        // We usually don't care if that's the case, so set a noop error handler
        localStorageService.remove('refresh');
        return $http.delete('api/v1/tokens/' + refreshToken).catch(() => {});
      }
    },
  };

  _.assign(service, {
    doLogin: (username, password) => {
      return $http.post('/api/v1/tokens', {
        username: username,
        password: password,
      }).then(
        (response) => {
          service.handleRefresh(response.data.refresh);
          service.handleToken(response.data.token);
        }
      );
    },
    doRefresh: (refreshToken) => {
      return $http.get('/api/v1/tokens/' + refreshToken).then(
        (response) => {
          service.handleToken(response.data.token);
        }
      );
    },
  });

  return service;
};
