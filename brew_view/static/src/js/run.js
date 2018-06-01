
import jwtDecode from 'jwt-decode';

appRun.$inject = [
  '$rootScope',
  '$state',
  '$stateParams',
  '$cookies',
  '$http',
  'localStorageService',
  'UtilityService',
  'SystemService',
];

/**
 * appRun - Runs the front-end application.
 * @param  {$rootScope} $rootScope         Angular's $rootScope object.
 * @param  {$state} $state                 Angular's $state object.
 * @param  {$stateParams} $stateParams     Angular's $stateParams object.
 * @param  {$cookies} $cookies             Angular's $cookies object.
 * @param  {UtilityService} UtilityService UtilityService for getting configuration/icons.
 * @param  {SystemService} SystemService   SystemService for getting all System information.
 */
export function appRun($rootScope, $state, $stateParams, $cookies, $http,
    localStorageService, UtilityService, SystemService) {
  $rootScope.$state = $state;
  $rootScope.$stateParams = $stateParams;

  // Change this to point to the Brew-View backend if it's at another location
  $rootScope.apiBaseUrl = '';

  // Set a default config and update it with config from the server
  $rootScope.config = {};
  UtilityService.getConfig().then(function(response) {
    let camelData = UtilityService.camelCaseKeys(response.data);
    angular.extend($rootScope.config, camelData);
    $rootScope.$broadcast('configLoaded');
  });

  // Use the SystemService to build the side bar.
  SystemService.getSystems().then(function(response) {
    $rootScope.systems = response.data;
    $rootScope.$broadcast('systemsLoaded');
  });

  $rootScope.themes = {
    'default': false,
    'slate': false,
  };

  $rootScope.logout = function() {
    localStorageService.remove('token');
    $http.defaults.headers.common.Authorization = undefined;

    $rootScope.userName = '';
  };

  $rootScope.changeTheme = function(theme) {
    $cookies.put('currentTheme', theme);
    for (const key of Object.keys($rootScope.themes)) {
      $rootScope.themes[key] = (key == theme);
    };
  };

  // Load up some cookies
  $rootScope.userName = $cookies.get('user_name');
  $rootScope.changeTheme($cookies.get('currentTheme') || 'default');
};


dtLoadingTemplate.$inject = ['DTDefaultOptions'];
/**
 * dtLoadingTemplate - Loading Template for datatabales
 * @param  {Object} DTDefaultOptions Data-tables default options.
 */
export function dtLoadingTemplate(DTDefaultOptions) {
  DTDefaultOptions.setLoadingTemplate('<div class="row"><loading loader="queues"></loading></div>');
};
