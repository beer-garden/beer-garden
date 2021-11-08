interceptorService.$inject = ["$rootScope", "$templateCache"];
/**
 * interceptorService - Used to intercept API requests.
 * @param  {$rootScope} $rootScope         Angular's $rootScope object.
 * @param  {$templateCache} $templateCache Angular's $templateCache object.
 */
export function interceptorService($rootScope, $templateCache) {
  /* eslint-disable no-invalid-this */
  let service = this;
  service.request = function (config) {
    // Only match things that we know are targeted at our backend
    if (
      $rootScope.apiBaseUrl &&
      (config.url.startsWith("config") ||
        config.url.startsWith("version") ||
        config.url.startsWith("api"))
    ) {
      config.url = $rootScope.apiBaseUrl + config.url;
    }

    return config;
  };
}

authInterceptorService.$inject = ["$q", "$injector"];
/**
 * authInterceptorService - Used to intercept API requests.
 * @param  {$q} $q                                   $q object
 * @param  {$injector} $injector                     $rootScope object
 * @return {Object}                                  Interceptor object
 */
export function authInterceptorService($q, $injector) {
  return {
    responseError: (rejection) => {
      // 401 means 'needs authentication'
      if (rejection.status === 401) {
        // Can't use normal dependency injection in here as it causes a cycle
        let $http = $injector.get("$http");
        let $rootScope = $injector.get("$rootScope");
        let TokenService = $injector.get("TokenService");

        // This attempts to handle the condition where an access token has
        // expired but there's a refresh token in storage. We use the refresh
        // token to get a new access token then re-attempt the original request.
        let refreshToken = TokenService.getRefresh();
        if (refreshToken) {
          return TokenService.doRefresh(refreshToken).then(
            (response) => {
              // Set the Authorization header to the updated default
              rejection.config.headers.Authorization =
                $http.defaults.headers.common.Authorization;

              // And retry the original request
              return $http(rejection.config);
            },
            (response) => {
              // Refresh didn't work. Maybe it was expired / removed
              // We're going to retry so clear the bad refresh token so we
              // don't get stuck in an infinite retry cycle
              $rootScope.doLogout();

              // Clear the Authorization header
              rejection.config.headers.Authorization = undefined;

              // And then retry the original request
              return $http(rejection.config);
            }
          );
        } else {
          // No refresh token - show the login modal
          // If this is a GET we're going to assume that retrying is taken care
          // of by the controllers handling the userChange event.
          // For other verbs we'll retry if the login is successful
          let loginModal = $rootScope.doLogin();
          if (rejection.config.method !== "GET") {
            return loginModal.result.then(
              (result) => {
                // At this point there'll be updated tokens, so set the
                // Authorization header to the updated default
                rejection.config.headers.Authorization =
                  $http.defaults.headers.common.Authorization;

                // And then retry the original request
                return $http(rejection.config);
              },
              () => {
                // User dismissed the modal so return the original rejection
                return $q.reject(rejection);
              }
            );
          }
        }
      }

      // Either the code wasn't 401 or we won't / can't retry
      // So just return the original rejection
      return $q.reject(rejection);
    },
  };
}

interceptorConfig.$inject = ["$httpProvider"];
/**
 * interceptorConfig - Angular configuration object for API interceptors.
 * @param  {$httpProvider} $httpProvider Angular's $httpProvider object.
 */
export function interceptorConfig($httpProvider) {
  $httpProvider.interceptors.push("APIInterceptor");
  $httpProvider.interceptors.push("authInterceptorService");
}
