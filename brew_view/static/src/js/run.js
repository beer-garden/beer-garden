import _ from 'lodash';
import {camelCaseKeys, responseState} from './services/utility_service.js';

import loginTemplate from '../templates/login.html';

appRun.$inject = [
  '$rootScope',
  '$state',
  '$stateParams',
  '$http',
  '$q',
  '$uibModal',
  'localStorageService',
  'UtilityService',
  'SystemService',
  'UserService',
  'TokenService',
  'RoleService',
  'EventService',
];

/**
 * appRun - Runs the front-end application.
 * @param  {$rootScope} $rootScope         Angular's $rootScope object.
 * @param  {$state} $state                 Angular's $state object.
 * @param  {$stateParams} $stateParams     Angular's $stateParams object.
 * @param  {$http} $http                   Angular's $http object.
 * @param  {$q} $q                         Angular's $q object.
 * @param  {Object} $uibModal              Angular UI's $uibModal object.
 * @param  {localStorageService} localStorageService Storage service
 * @param  {UtilityService} UtilityService Service for configuration/icons.
 * @param  {SystemService} SystemService   Service for System information.
 * @param  {UserService} UserService       Service for User information.
 * @param  {TokenService} TokenService     Service for Token information.
 * @param  {RoleService} RoleService       Service for Role information.
 */
export default function appRun(
    $rootScope,
    $state,
    $stateParams,
    $http,
    $q,
    $uibModal,
    localStorageService,
    UtilityService,
    SystemService,
    UserService,
    TokenService,
    RoleService,
    EventService) {
  $rootScope.$state = $state;
  $rootScope.$stateParams = $stateParams;

  let loginModal;
  $rootScope.loginInfo = {};

  // Change this to point to the Brew-View backend if it's at another location
  $rootScope.apiBaseUrl = '';

  $rootScope.config = {};
  $rootScope.systems = [];

  $rootScope.themes = {
    'default': false,
    'slate': false,
  };

  $rootScope.responseState = responseState;

  $rootScope.loadConfig = function() {
    $rootScope.configPromise = UtilityService.getConfig().then(
      (response) => {
        angular.extend($rootScope.config, camelCaseKeys(response.data));
      },
      (response) => {
        return $q.reject(response);
      }
    );
    return $rootScope.configPromise;
  };

  $rootScope.loadUser = function(token) {
    $rootScope.userPromise = UserService.loadUser(token).then(
      (response) => {
        // Angular doesn't do a deep watch here, so make sure we calculate
        // and set the permissions before setting $rootScope.user
        let user = response.data;

        // coalescePermissions [0] is roles, [1] is permissions
        user.permissions = RoleService.coalescePermissions(user.roles)[1];

        let theme = _.get(user, 'preferences.theme', 'default');
        $rootScope.changeTheme(theme);

        $rootScope.user = user;
      }, (response) => {
        return $q.reject(response);
      }
    );
    return $rootScope.userPromise;
  };

  $rootScope.loadSystems = function() {
    $rootScope.systemsPromise = SystemService.getSystems(
        false, 'id,name,version').then(
      (response) => {
        $rootScope.systems = response.data;
      },
      (response) => {
        $rootScope.systems = [];

        // This is super annoying.
        // If any controller is actually using this promise we need to return a
        // rejection here, otherwise the chained promise will actually resolve
        // (success callback will be invoked instead of failure callback).
        // But for controllers that don't care if this fails (like the landing
        // controller) this causes a 'possibly unhandled rejection' since they
        // haven't constructed a pipeline based on this promise.
        return $q.reject(response);
      }
    );
    return $rootScope.systemsPromise;
  };

  $rootScope.changeUser = function(token) {
    // We need to reload systems as those permisisons could have changed
    $rootScope.loadSystems();

    $rootScope.loadUser(token).then(
      () => {
        $rootScope.$broadcast('userChange');
      }
    );
  };

  $rootScope.initialLoad = function() {
    // Very first thing is to load up a token if one exists
    let token = localStorageService.get('token');
    if (token) {
      TokenService.handleToken(token);
    }

    $rootScope.loadConfig();
    $rootScope.loadSystems();
    $rootScope.loadUser(token).catch(
      // This prevents the situation where the user needs to logout but the
      // logout button isn't displayed because there's no user loaded
      // (happens if the server secret changes)
      (response) => {
        $rootScope.doLogout();
      }
    );

    EventService.connect();
  };

  $rootScope.hasPermission = function(user, permissions) {
    if (!$rootScope.config.authEnabled) return true;
    if (_.isUndefined(user)) return false;
    if (_.includes(user.permissions, 'bg-all')) return true;

    // This makes it possible to pass an array or a single string
    return _.intersection(
      user.permissions, _.castArray(permissions)
    ).length;
  };

  $rootScope.changeTheme = function(theme, sendUpdate) {
    localStorageService.set('currentTheme', theme);
    for (const key of Object.keys($rootScope.themes)) {
      $rootScope.themes[key] = (key == theme);
    };

    if ($rootScope.isUser($rootScope.user) && sendUpdate) {
      UserService.setTheme($rootScope.user.id, theme);
    }
  };

  $rootScope.isUser = function(user) {
    return user && user.username !== 'anonymous';
  };

  $rootScope.doLogin = function() {
    if (!loginModal) {
      loginModal = $uibModal.open({
        controller: 'LoginController',
        size: 'sm',
        template: loginTemplate,
      });
      loginModal.result.then(
        () => {
          $rootScope.changeUser(TokenService.getToken());
        },
        _.noop // Prevents annoying console log messages
      );
      loginModal.closed.then(
        () => {
          loginModal = undefined;
        }
      );
    }
    return loginModal;
  };

  $rootScope.doLogout = function() {
    TokenService.clearToken();
    TokenService.clearRefresh();

    $rootScope.changeUser(undefined);
  };

  $rootScope.setWindowTitle = function(...titleParts) {
    $rootScope.configPromise.then(
      () => {
        titleParts.push($rootScope.config.applicationName);
        $rootScope.title = _.join(titleParts, ' - ');
      }
    );
  };

  /**
   * Compare two system versions. Intended to be used for sorting.
   *
   * Newer systems will be sorted to the front. For example, this would be the
   * result of sorting with this function:
   *
   * [ "1.1.0.dev0", "1.0.0", "1.0.0.dev1", "1.0.0.dev0", "1.0.0.dev" ]
   *
   * Note that versions with less parts are considered newer.
   *
   * @param {string} version1 - first version
   * @param {string} version2 - second version
   * @return {int} - result of comparison
   */
  const compareVersions = function(version1, version2) {
    let parts1 = version1.split('.');
    let parts2 = version2.split('.');

    let numParts = Math.min(parts1.length, parts2.length);

    for (let i = 0; i < numParts; i++) {
      let intPart1 = parseInt(parts1[i]);
      let intPart2 = parseInt(parts2[i]);

      if (!isNaN(intPart1) && !isNaN(intPart2)) {
        if (intPart1 > intPart2) {
          return -1;
        } else if (intPart1 < intPart2) {
          return 1;
        }
      } else {
        if (parts1[i] > parts2[i]) {
          return -1;
        } else if (parts1[i] < parts2[i]) {
          return 1;
        }
      }
    }

    if (parts1.length < parts2.length) {
      return -1;
    } else if (parts1.length > parts2.length) {
      return 1;
    }

    return 0;
  };

  /**
   * Converts a system's version to the 'latest' semantic url scheme.
   * @param {Object} system - system for which you want the version URL.
   * @return {string} - either the system's version or 'latest'.
   */
  $rootScope.getVersionForUrl = function(system) {
    // All versions for systems with the given system name
    let versions = _.map(
      _.filter($rootScope.systems, {name: system.name}),
      _.property('version')
    );

    // Sorted according to the system comparison function
    let sorted = versions.sort(compareVersions);

    return system.version == sorted[0] ? 'latest' : system.version;
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
    let notFound = {
      data: {message: 'No matching system'},
      errorGroup: 'system',
      status: 404,
    };

    return $rootScope.systemsPromise.then(
      () => {
        if (version !== 'latest') {
          let sys = _.find($rootScope.systems, {name: name, version: version});

          if (_.isUndefined(sys)) {
            return $q.reject(notFound);
          } else {
            return $q.resolve(sys);
          }
        }

        let filteredSystems = _.filter($rootScope.systems, {name: name});
        if (_.isEmpty(filteredSystems)) {
          return $q.reject(notFound);
        }

        let versions = _.map(filteredSystems, _.property('version'));
        let sorted = versions.sort(compareVersions);

        return $q.resolve(_.find(filteredSystems, {version: sorted[0]}));
      }
    );
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

  $rootScope.initialLoad();
};
