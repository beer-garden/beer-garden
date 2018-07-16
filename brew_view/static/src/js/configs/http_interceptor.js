
interceptorService.$inject = ['$rootScope', '$templateCache'];
/**
 * interceptorService - Used to intercept API requests.
 * @param  {$rootScope} $rootScope         Angular's $rootScope object.
 * @param  {$templateCache} $templateCache Angular's $templateCache object.
 */
export function interceptorService($rootScope, $templateCache) {
  /* eslint-disable no-invalid-this */
  let service = this;
  service.request = function(config) {
    // Only match things that we know are targeted at our backend
    if ($rootScope.apiBaseUrl && (config.url.startsWith('config') ||
        config.url.startsWith('version') || config.url.startsWith('api'))) {
      config.url = $rootScope.apiBaseUrl + config.url;
    }
    return config;
  };
};

authInterceptorService.$inject = ['$q', '$injector', 'localStorageService'];
/**
 * authInterceptorService - Used to intercept API requests.
 * @param  {$q} $q                                   $q object
 * @param  {$injector} $injector                     $rootScope object
 * @param  {localStorageService} localStorageService Storage service
 * @return {Object}                                  Interceptor object
 */
export function authInterceptorService($q, $injector, localStorageService) {
  return {
    responseError: (rejection) => {
      // This attempts to handle the condition where an access token has expired
      // but there's a refresh token in storage. We use the refresh token to get
      // a new access token and then re-attempt the original request.
      if (rejection.status === 401) {
        let refreshToken = localStorageService.get('refresh');

        if (refreshToken) {
          // Thanks for this angular - can't inject this as it causes a cycle
          let $http = $injector.get('$http');

          return $http.get('/api/v1/tokens/'+refreshToken)
          .then((response) => {
            let newToken = response.data.token;
            localStorageService.set('token', newToken);

            let newHeader = 'Bearer ' + newToken;
            $http.defaults.headers.common.Authorization = newHeader;
            rejection.config.headers.Authorization = newHeader;

            return $http(rejection.config);
          });
        }
      }

      // Some other error, just return the rejection
      return $q.reject(rejection);
    },
  };
};

interceptorConfig.$inject = ['$httpProvider'];
/**
 * interceptorConfig - Angular configuration object for API interceptors.
 * @param  {$httpProvider} $httpProvider Angular's $httpProvider object.
 */
export function interceptorConfig($httpProvider) {
  $httpProvider.interceptors.push('APIInterceptor');
  $httpProvider.interceptors.push('authInterceptorService');
};
