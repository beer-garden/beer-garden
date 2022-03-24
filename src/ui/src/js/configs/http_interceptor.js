interceptorService.$inject = ['$rootScope', '$templateCache'];
/**
 * interceptorService - Used to intercept API requests.
 * @param  {$rootScope} $rootScope         Angular's $rootScope object.
 * @param  {$templateCache} $templateCache Angular's $templateCache object.
 */
export function interceptorService($rootScope, $templateCache) {
  /* eslint-disable no-invalid-this */
  const service = this;
  service.request = function(config) {
    // Only match things that we know are targeted at our backend
    if (
      $rootScope.apiBaseUrl &&
      (config.url.startsWith('config') ||
        config.url.startsWith('version') ||
        config.url.startsWith('api'))
    ) {
      config.url = $rootScope.apiBaseUrl + config.url;
    }

    return config;
  };
}

authInterceptorService.$inject = ['$q', '$injector'];
/**
 * authInterceptorService - Used to intercept API requests.
 * @param  {$q} $q                                   $q object
 * @param  {$injector} $injector                     $rootScope object
 * @return {Object}                                  Interceptor object
 */
export function authInterceptorService($q, $injector) {
  let inFlightAuthRequest = null;

  const doLogin = function(rejection) {
    const $rootScope = $injector.get('$rootScope');
    const loginModal = $rootScope.doLogin();

    if (rejection.config.method !== 'GET') {
      return loginModal.result.then(
          () => {
            // noop; modal will refresh the page
          },
          () => {
            // User dismissed the modal so return the original rejection
            return $q.reject(rejection);
          },
      );
    }
  };

  return {
    responseError: (rejection) => {
      // 401 means 'needs authentication'
      if (rejection.status === 401) {
        // Can't use normal dependency injection in here as it causes a cycle
        const $http = $injector.get('$http');
        const $rootScope = $injector.get('$rootScope');
        const TokenService = $injector.get('TokenService');

        const deferred = $q.defer();

        // This attempts to handle the condition where an access token has
        // expired but there's a refresh token in storage. We use the refresh
        // token to get a new access token then re-attempt the original request.
        const refreshToken = TokenService.getRefresh();
        if (refreshToken) {
          if (!inFlightAuthRequest) {
            inFlightAuthRequest = TokenService.doRefresh(refreshToken);
          }

          inFlightAuthRequest.then((response) => {
            inFlightAuthRequest = null;

            // Set the Authorization header to the updated default
            rejection.config.headers.Authorization =
              $http.defaults.headers.common.Authorization;

            // And retry the original request
            $http(rejection.config).then(
                (response) => {
                  deferred.resolve(response);
                },
                (response) => {
                  deferred.reject();
                },
            );
          });

          return deferred.promise;
        } else {
          // If trusted header authentication is available, just try to login
          // without opening the modal.
          if ($rootScope.config.trustedHeaderAuthEnabled) {
            if (!inFlightAuthRequest) {
              inFlightAuthRequest = TokenService.doLogin();
            }

            return inFlightAuthRequest.then(
                ()=> {
                  inFlightAuthRequest = null;
                  // login succeeded, reload the page
                  location.reload();
                }, () => {
                  // login failed, open the login modal
                  return doLogin(rejection);
                },
            );
          } else {
            return doLogin(rejection);
          }
        }
      }

      // Either the code wasn't 401 or we won't / can't retry
      // So just return the original rejection
      return $q.reject(rejection);
    },
  };
}

interceptorConfig.$inject = ['$httpProvider'];
/**
 * interceptorConfig - Angular configuration object for API interceptors.
 * @param  {$httpProvider} $httpProvider Angular's $httpProvider object.
 */
export function interceptorConfig($httpProvider) {
  $httpProvider.interceptors.push('APIInterceptor');
  $httpProvider.interceptors.push('authInterceptorService');
}
