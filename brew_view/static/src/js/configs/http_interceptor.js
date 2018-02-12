
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

interceptorConfig.$inject = ['$httpProvider'];

/**
 * interceptorConfig - Angular configuration object for API interceptors.
 * @param  {$httpProvider} $httpProvider Angular's $httpProvider object.
 */
export function interceptorConfig($httpProvider) {
  $httpProvider.interceptors.push('APIInterceptor');
};
