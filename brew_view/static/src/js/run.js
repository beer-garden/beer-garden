
appRun.$inject = [
  '$rootScope',
  '$state',
  '$stateParams',
  '$cookies',
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
export function appRun($rootScope, $state, $stateParams, $cookies, UtilityService, SystemService) {
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
  SystemService.getSystems(undefined, 'id,name,version').then(function(response) {
    $rootScope.systems = response.data;
    $rootScope.$broadcast('systemsLoaded');
  });

  $rootScope.themes = {
    'default': false,
    'slate': false,
  };

  $rootScope.changeTheme = function(theme) {
    $cookies.put('currentTheme', theme);
    for (const key of Object.keys($rootScope.themes)) {
      $rootScope.themes[key] = (key == theme);
    };
  };

  // Uses cookies to get the current theme
  $rootScope.changeTheme($cookies.get('currentTheme') || 'default');

  const isLaterVersion = function(system1, system2) {
    let versionParts1 = system1.version.split('.');
    let versionParts2 = system2.version.split('.');

    for (let i = 0; i < 3; i++) {
      if (parseInt(versionParts1[i]) > parseInt(versionParts2[i])) {
        return true;
      }
    }
    return false;
  };

  /**
   * Converts a system's version to the 'latest' semantic url scheme.
   * @param {Object} system  - system for which you want the version URL.
   * @return {string} - either the systems version or 'latest'.
   */
  $rootScope.getVersionForUrl = function(system) {
    for (let sys of $rootScope.systems) {
      if (sys.name == system.name) {
        if (isLaterVersion(sys, system)) {
          return system.version;
        }
      }
    }
    return 'latest';
  };


  /**
   * Convert a system ObjectID to a route to use for the router.
   * @param {string} systemId  - ObjectID for system.
   * @return {string} url to use for UI routing.
   */
  $rootScope.getSystemUrl = function(systemId) {
    for (let system of $rootScope.systems) {
      if (system.id == systemId) {
        let version = this.getVersionForUrl(system);
        return '/systems/' + system.name + '/' + version;
      }
    }
    return '/systems';
  };

  /**
   * Find the system with the specified name/version (version can just
   * be the string 'latest')
   *
   * @param {string} name - The name of the system you wish to find.
   * @param {string} version - The version you want to find (or latest)
   * @return {Object} The latest system or undefined if it is not found.
   */
  $rootScope.findSystem = function(name, version) {
    let latestSystem;
    for (let system of $rootScope.systems) {
      if (system.name === name) {
        if (!angular.isDefined(latestSystem)) {
          latestSystem = system;
        }

        if (system.version === version) {
          return system;
        } else if (version === 'latest' && isLaterVersion(system, latestSystem)) {
          latestSystem = system;
        }
      }
    }
    return latestSystem;
  };


  /**
   * Find the system with the given ID.
   * @param {string} systemId - System's ObjectID
   * @return {Object} the system with this ID.
   */
  $rootScope.findSystemByID = function(systemId) {
    for (let system of $rootScope.systems) {
      if (system.id === systemId) {
        return system;
      }
    }
  };
};


dtLoadingTemplate.$inject = ['DTDefaultOptions'];
/**
 * dtLoadingTemplate - Loading Template for datatabales
 * @param  {Object} DTDefaultOptions Data-tables default options.
 */
export function dtLoadingTemplate(DTDefaultOptions) {
  DTDefaultOptions.setLoadingTemplate('<div class="row"><loading loader="queues"></loading></div>');
};
