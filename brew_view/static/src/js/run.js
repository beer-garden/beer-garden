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
 * @param  {TokenService} TokenService     Service for User information.
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
    RoleService) {
  $rootScope.$state = $state;
  $rootScope.$stateParams = $stateParams;

  $rootScope.loginInfo = {};
  $rootScope.loginError = false;

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

    // And actually return this promise so we can broadcast in certain cases
    return $rootScope.loadUser(token);
  };

  $rootScope.initialLoad = function() {
    // Very first thing is to load up a token if one exists
    let token = localStorageService.get('token');
    if (token) {
      TokenService.handleToken(token);
    }

    $rootScope.loadConfig().then(
      $rootScope.changeUser(token)
    ).then(
      () => {
        $rootScope.setWindowTitle();
      }
    );
  };

  $rootScope.doLogout = function() {
    let refreshToken = localStorageService.get('refresh');
    if (refreshToken) {
      TokenService.clearRefresh(refreshToken);
      localStorageService.remove('refresh');
    }

    localStorageService.remove('token');
    $http.defaults.headers.common.Authorization = undefined;

    $rootScope.changeUser(undefined).then(
      () => {
        $rootScope.$broadcast('userChange');
      }
    );
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
    // Clicking should always clear the red outline
    $rootScope.loginError = false;

    let modalInstance = $uibModal.open({
      controller: 'LoginController',
      size: 'sm',
      template: loginTemplate,
    });

    modalInstance.result.then(
      (create) => {
        RoleService.createRole(create).then(loadAll);
      },
      // We don't really need to do anything if canceled
      () => {}
    );
  };

  $rootScope.setWindowTitle = function(...titleParts) {
    $rootScope.configPromise.then(
      () => {
        titleParts.push($rootScope.config.applicationName);
        $rootScope.title = _.join(titleParts, ' - ');
      }
    )
  };

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

        let latestSystem = filteredSystems[0];
        for (let system of $rootScope.systems) {
          if (isLaterVersion(system, latestSystem)) {
            latestSystem = system;
          }
        }

        return $q.resolve(latestSystem);
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
