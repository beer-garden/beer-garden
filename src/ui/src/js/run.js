import $ from 'jquery';
import _ from 'lodash';
import {responseState} from './services/utility_service.js';

import changePasswordTemplate from '../templates/change_password.html';
import loginTemplate from '../templates/login.html';

window.$ = $;
window._ = _;

appRun.$inject = [
  '$rootScope',
  '$state',
  '$stateParams',
  '$http',
  '$q',
  '$uibModal',
  '$transitions',
  '$interval',
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
 * @param  {Object} $rootScope           Angular's $rootScope object.
 * @param  {Object} $state               Angular's $state object.
 * @param  {Object} $stateParams         Angular's $stateParams object.
 * @param  {Object} $http                Angular's $http object.
 * @param  {Object} $q                   Angular's $q object.
 * @param  {Object} $uibModal            Angular UI's $uibModal object.
 * @param  {Object} $transitions         Angular's $transitions object.
 * @param  {Object} $interval            Angular's $interval object.
 * @param  {Object} localStorageService  Storage service
 * @param  {Object} UtilityService       Service for configuration/icons.
 * @param  {Object} SystemService        Service for System information.
 * @param  {Object} UserService          Service for User information.
 * @param  {Object} TokenService         Service for Token information.
 * @param  {Object} RoleService          Service for Role information.
 * @param  {Object} EventService         Service for Event information.
 */
export default function appRun(
    $rootScope,
    $state,
    $stateParams,
    $http,
    $q,
    $uibModal,
    $transitions,
    $interval,
    localStorageService,
    UtilityService,
    SystemService,
    UserService,
    TokenService,
    RoleService,
    EventService,
) {
  $rootScope.$state = $state;
  $rootScope.$stateParams = $stateParams;

  let loginModal;
  $rootScope.loginInfo = {};

  // Change this to point to the Brew-View backend if it's at another location
  $rootScope.apiBaseUrl = '';

  $rootScope.config = {};

  $rootScope.config.defaultHome = 'base.systems()';
  $rootScope.config.defaultHomePage = 'base.systems';
  $rootScope.config.defaultHomeParameters = {};

  $rootScope.themes = {
    default: false,
    slate: false,
  };

  $rootScope.menu_page = 'main';

  $rootScope.responseState = responseState;

  $rootScope.getIcon = UtilityService.getIcon;

  $rootScope.loadUser = function(token) {
    $rootScope.userPromise = UserService.loadUser(token).then(
        (response) => {
        // Angular doesn't do a deep watch here, so make sure we calculate
        // and set the permissions before setting $rootScope.user
          const user = response.data;

          // If user is logged in, change to their default theme selection
          let theme;
          if (user.id) {
            theme = _.get(user, 'preferences.theme', 'default');
          } else {
            theme = localStorageService.get('currentTheme') || 'default';
          }
          $rootScope.changeTheme(theme, false);

          $rootScope.user = user;
        },
        (response) => {
          return $q.reject(response);
        },
    );
    return $rootScope.userPromise;
  };

  $rootScope.changeUser = function(token) {
    // // We need to reload systems as those permisisons could have changed
    // SystemService.loadSystems();

    $rootScope.loadUser(token).then(() => {
      // $rootScope.$broadcast('userChange');
    });
  };

  $rootScope.initialLoad = function() {
    // Very first thing is to load up a token if one exists
    const token = TokenService.getToken();
    const refreshToken = TokenService.getRefresh();

    if (token) {
      TokenService.handleToken(token);
      $rootScope.changeUser(TokenService.getToken());
    } else if (refreshToken) {
      TokenService.doRefresh(refreshToken).then(() => {
        $rootScope.changeUser(TokenService.getToken());
      });
    }

    // Connect to the event socket
    EventService.connect();

    // Load theme from local storage
    // REMOVE THIS ONCE THE rootScope.loadUser CALL BELOW IS ENABLED
    const theme = localStorageService.get('currentTheme') || 'default';
    $rootScope.changeTheme(theme, false);

    $rootScope.config.defaultHome = localStorageService.get('defaultHome') || 'base.systems()';
    $rootScope.config.defaultHomePage = localStorageService.get('defaultHomePage') || 'base.systems';
    $rootScope.config.defaultHomeParameters = localStorageService.get('defaultHomeParameters') || {};

    // $rootScope.loadUser(token).catch(
    //   // This prevents the situation where the user needs to logout but the
    //   // logout button isn't displayed because there's no user loaded
    //   // (happens if the server secret changes)
    //   (response) => {
    //     $rootScope.doLogout();
    //   }
    // );
  };

  $rootScope.hasPermission = function(user, permission) {
    if (!$rootScope.config.authEnabled) return true;
    if (_.isUndefined(user)) return false;

    return UserService.hasPermission(user, permission);
  };

  $rootScope.hasGardenPermission = function(user, permission, garden) {
    if (!$rootScope.config.authEnabled) return true;
    if (_.isUndefined(user)) return false;

    return UserService.hasGardenPermission(user, permission, garden);
  };

  $rootScope.hasSystemPermission = function(user, permission, system) {
    if (!$rootScope.config.authEnabled) return true;
    if (_.isUndefined(user)) return false;

    return UserService.hasSystemPermission(user, permission, system);
  };

  $rootScope.hasCommandPermission = function(user, permission, command) {
    if (!$rootScope.config.authEnabled) return true;
    if (_.isUndefined(user)) return false;

    return UserService.hasCommandPermission(user, permission, command);
  };

  $rootScope.hasJobPermission = function(user, permission, job) {
    if (!$rootScope.config.authEnabled) return true;
    if (_.isUndefined(user)) return false;

    return UserService.hasJobPermission(user, permission, job);
  };

  $rootScope.changeTheme = function(theme, sendUpdate) {
    localStorageService.set('currentTheme', theme);
    for (const key of Object.keys($rootScope.themes)) {
      $rootScope.themes[key] = key == theme;
    }

    if ($rootScope.isUser($rootScope.user) && sendUpdate) {
      UserService.setTheme($rootScope.user.id, theme);
    }
  };

  $rootScope.setHomeToCurrent = function() {
    let params = $rootScope.$stateParams;
    let page = $rootScope.$state.router.globals.current.name;

    let homeParameters = {};

    for (var key in params){
      if(params[key] != null && !key.startsWith("$")){
        homeParameters[key] = params[key];
      }
    }

    let paramsString = $rootScope.convertDictToJson(homeParameters);

    let newHomePage = null;
    if(paramsString == null){
      newHomePage = `${page}()`;
    } else {
      newHomePage = `${page}(${paramsString})`;
    }

    localStorageService.set('defaultHome', newHomePage);
    localStorageService.set('defaultHomePage', page);
    localStorageService.set('defaultHomeParameters', homeParameters);

    $rootScope.config.defaultHome = newHomePage;
    $rootScope.config.defaultHomePage = page;
    $rootScope.config.defaultHomeParameters = homeParameters;

    location.reload();
  }

  $rootScope.convertDictToJson = function(dictObject) {
    let jsonString = null;
    for (var key in dictObject){
      if (dictObject[key != null] && !key.startsWith("$")){
        if (typeof dictObject[key] == "string" || dictObject[key] instanceof String){
          if (jsonString == null){
            jsonString = `${key} : "${dictObject[key]}"`;
          } else {
            jsonString = `${jsonString}, ${key} : "${dictObject[key]}"`;
          }
        }
        else if (typeof dictObject[key] == "object" || dictObject[key] instanceof Object){
          if (jsonString == null){
            jsonString = `${key} : ${$rootScope.convertDictToJson(dictObject[key])}`;
          } else {
            jsonString = `${jsonString}, ${key} : ${$rootScope.convertDictToJson(dictObject[key])}`;
          }
        } else {
          if (jsonString == null){
            jsonString = `${key} : ${dictObject[key]}`;
          } else {
            jsonString = `${jsonString}, ${key} : ${dictObject[key]}`;
          }
        }
      }
    }

    if (jsonString == null){
      return null;
    }

    return `{${jsonString}}`;
  }

  $rootScope.getHome = function() {
    return $rootScope.config.defaultHome;
  }

  $rootScope.authEnabled = function() {
    return $rootScope.config.authEnabled;
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
            location.reload();
          },
          _.noop, // Prevents annoying console log messages
      );
      loginModal.closed.then(() => {
        loginModal = undefined;
      });
      loginModal.closed.then(() => {
        loginModal = undefined;
      });
    }
    return loginModal;
  };

  $rootScope.doLogout = function() {
    TokenService.clearToken();
    TokenService.clearRefresh();

    $rootScope.changeUser(undefined);
    location.reload();
  };

  $rootScope.setWindowTitle = function(...titleParts) {
    titleParts.push($rootScope.config.applicationName);
    $rootScope.title = _.join(titleParts, ' - ');
  };

  $transitions.onSuccess({to: 'base'}, () => {
    $state.go($rootScope.config.defaultHomePage, $rootScope.config.defaultHomeParameters);
  });

  $rootScope.setMenuPage = function(page) {
    $rootScope.menu_page = page;
  };

  $rootScope.checkMenuPage = function(page) {
    return $rootScope.menu_page == page;
  };

  $rootScope.doChangePassword = function() {
    return $uibModal.open({
      controller: 'ChangePasswordController',
      size: 'sm',
      template: changePasswordTemplate,
    }).result.then(
        _.noop,
        _.noop,
    );
  };

  function upsertSystem(system) {
    const index = _.findIndex($rootScope.systems, {id: system.id});

    if (index == -1) {
      $rootScope.systems.push(system);
    } else {
      $rootScope.systems.splice(index, 1, system);
    }
  }

  function removeSystem(system) {
    const index = _.findIndex($rootScope.systems, {id: system.id});

    if (index != -1) {
      $rootScope.systems.splice(index, 1);
    }
  }

  function updateInstance(instance) {
    _.forEach($rootScope.systems, (sys) => {
      const index = _.findIndex(sys.instances, {id: instance.id});

      if (index != -1) {
        sys.instances.splice(index, 1, instance);

        // Returning false ends the iteration early
        return false;
      }
    });
  }

  EventService.addCallback('global_systems', (event) => {
    if (['SYSTEM_CREATED', 'SYSTEM_UPDATED'].includes(event.name)) {
      upsertSystem(event.payload);
    } else if (event.name == 'SYSTEM_REMOVED') {
      removeSystem(event.payload);
    } else if (event.name.startsWith('INSTANCE')) {
      updateInstance(event.payload);
    }
  });

  EventService.addCallback('websocket_authorization', (event) => {
    if (event.name === 'AUTHORIZATION_REQUIRED') {
      EventService.updateToken(TokenService.getToken());
    }
  });

  $interval(
      function() {
        EventService.connect(TokenService.getToken());
      },
      5000,
      0,
      false,
  );

  $interval(
      function() {
        TokenService.preemptiveRefresh();
      },
      30000,
      0,
      false,
  );

  $rootScope.initialLoad();
}
