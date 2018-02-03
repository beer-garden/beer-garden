
interceptorService.$inject = ['$rootScope', '$templateCache'];
export function interceptorService($rootScope, $templateCache) {
  var service = this;
  service.request = function(config) {
    // Only match things that we know are targeted at our backend
    if($rootScope.apiBaseUrl && (config.url.startsWith('config') ||
        config.url.startsWith('version') || config.url.startsWith('api'))) {
      config.url = $rootScope.apiBaseUrl + config.url;
    }
    return config;
  };
};

interceptorConfig.$inject = ['$httpProvider'];
export function interceptorConfig($httpProvider){
  $httpProvider.interceptors.push('APIInterceptor');
};
