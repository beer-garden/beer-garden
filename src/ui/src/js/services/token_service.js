import _ from 'lodash';
import jwtDecode from 'jwt-decode';

tokenService.$inject = ['$http', 'storageService', 'EventService'];

/**
 * tokenService - Service for interacting with the token API.
 * @param  {Object} $http               Angular's $http Object.
 * @param  {Object} storageService      Storage service
 * @param  {Object} EventService        Websocket event handling service
 * @return {Object}       Service for interacting with the token API.
 */
export default function tokenService($http, storageService, EventService) {
  const service = {
    getToken: () => {
      return storageService.get('token', null);
    },
    preemptiveRefresh: () => {
      const token = service.getToken();

      if (token) {
        const exp = jwtDecode(token).exp;
        const expDate = new Date(exp * 1000);
        const curDate = new Date();
        const minDelta = (expDate - curDate) / (1000 * 60);

        if (minDelta <= 2) {
          service.doRefresh(service.getRefresh());
        }
      }
    },
    handleToken: (token) => {
      storageService.set('token', token);
      $http.defaults.headers.common.Authorization = 'Bearer ' + token;
    },
    clearToken: () => {
      storageService.remove('token');
      $http.defaults.headers.common.Authorization = undefined;
    },
    revokeUserToken: (userName) => {
      return $http.delete('api/v1/tokens/' + userName);
    },
    getRefresh: () => {
      return storageService.get('refresh', null);
    },
    handleRefresh: (refreshToken) => {
      storageService.set('refresh', refreshToken);
    },
    clearRefresh: () => {
      const refreshToken = storageService.get('refresh', null);
      if (refreshToken) {
        // It's possible the refresh token was already removed from the database
        // We usually don't care if that's the case, so set a noop error handler
        storageService.remove('refresh');
        return $http
            .post('api/v1/token/revoke', {refresh: refreshToken})
            .catch(() => {});
      }
    },
  };

  _.assign(service, {
    doLogin: (username, password) => {

      let headers = {};
      
      if (username !== null && password !== null) {
        headers = {
          username: username,
          password: password,
        };
      }
      
      return $http
          .post('api/v1/token', headers)
          .then((response) => {
            service.handleRefresh(response.data.refresh);
            service.handleToken(response.data.access);
          });
    },
    doRefresh: (refreshToken) => {
      return $http
          .post('api/v1/token/refresh', {refresh: refreshToken})
          .then(
              (response) => {
                service.handleRefresh(response.data.refresh);
                service.handleToken(response.data.access);
                EventService.updateToken(response.data.access);
              },
              (response) => {
                service.clearRefresh();
                service.clearToken();
              },
          );
    },
  });

  return service;
}
