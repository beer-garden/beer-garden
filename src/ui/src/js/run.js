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
  '$transitions',
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
    $transitions,
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
  $rootScope.namespaces = [];
  $rootScope.currentNamespace = undefined;

  $rootScope.themes = {
    'default': false,
    'slate': false,
  };

  $rootScope.responseState = responseState;

  $rootScope.getIcon = UtilityService.getIcon;

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

  $rootScope.changeUser = function(token) {
    // // We need to reload systems as those permisisons could have changed
    // SystemService.loadSystems();

    $rootScope.loadUser(token).then(
      () => {
        $state.reload();
        // $rootScope.$broadcast('userChange');
      }
    );
  };

  $rootScope.initialLoad = function() {
    // Very first thing is to load up a token if one exists
    let token = localStorageService.get('token');
    if (token) {
      TokenService.handleToken(token);
    }
    else {
        // Attempt login through Certs
        TokenService.doLogin(null, null);
        let token = localStorageService.get('token');
    }

    $rootScope.loadUser(token).catch(
      // This prevents the situation where the user needs to logout but the
      // logout button isn't displayed because there's no user loaded
      // (happens if the server secret changes)
      (response) => {
        $rootScope.doLogout();
      }
    ).then(
        () => {
            $state.reload();
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

  $rootScope.getCurrentNamespace = function() {
    return $rootScope.currentNamespace;
  };

  $rootScope.setCurrentNamespace = (namespace) => {
    $rootScope.currentNamespace = namespace;
  };

  $rootScope.isCurrentNamespace = function(namespace) {
    return $rootScope.currentNamespace == namespace;
  };

  $rootScope.changeNamespace = (namespace) => {
    let cur_state = $state.current.name;

    $state.go(
      cur_state === "base.landing" ? "base.namespace.systems" : cur_state,
      {namespace: namespace}
    );
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
    titleParts.push($rootScope.config.applicationName);
    $rootScope.title = _.join(titleParts, ' - ');
  };

  $rootScope.mainButton = () => {
    if ($stateParams.namespace) {
      $state.go('base.namespace.systems');
    } else {
      $state.go('base.landing');
    }
  };

  $transitions.onStart({}, (transition, state) => {
    $rootScope.setCurrentNamespace(transition.params('to').namespace);
  });

  $transitions.onSuccess({entering: 'base.namespace'}, (transition) => {
    EventService.close();
    EventService.connect();
  });

  $transitions.onSuccess({to: 'base'}, () => {
    $state.go('base.landing');
  });

  $rootScope.initialLoad();
};
