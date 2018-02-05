
appRun.$inject = ['$rootScope', '$state', '$stateParams', '$cookies', 'UtilityService', 'SystemService'];
export function appRun($rootScope, $state, $stateParams, $cookies, UtilityService, SystemService) {
  $rootScope.$state = $state;
  $rootScope.$stateParams = $stateParams;

  // Change this to point to the Brew-View backend if it's at another location
  $rootScope.apiBaseUrl = '';

  // Set a default config and update it with config from the server
  $rootScope.config = {};
  UtilityService.getConfig().then(function(response) {
    angular.extend($rootScope.config, response.data);
    $rootScope.$broadcast('configLoaded');
  });

  // Use the SystemService to build the side bar.
  SystemService.getSystems().then(function(response) {
    $rootScope.systems = response.data;
    $rootScope.$broadcast('systemsLoaded');
  });

  $rootScope.themes = {
    "default": false,
    "slate": false
  };

  $rootScope.changeTheme = function(theme){
    $cookies.put('currentTheme', theme);
    for (var key in $rootScope.themes) {
      $rootScope.themes[key] = (key == theme);
    }
  };

  // Uses cookies to get the current theme
  $rootScope.changeTheme($cookies.get('currentTheme') || 'default');
};

dtLoadingTemplate.$inject = ['DTDefaultOptions'];
export function dtLoadingTemplate(DTDefaultOptions) {
  DTDefaultOptions.setLoadingTemplate('<div class="row"><loading loader="queues"></loading></div>');
};
