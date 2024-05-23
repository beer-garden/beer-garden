import $ from 'jquery';
import _ from 'lodash';
import {responseState, camelCaseKeys}  from './services/utility_service.js';

import changePasswordTemplate from '../templates/change_password.html';
import loginTemplate from '../templates/login.html';

window.$ = $;
window._ = _;

appRun.$inject = [
  '$rootScope',
  '$state',
  '$stateParams',
  '$http',
  '$location',
  '$q',
  '$uibModal',
  '$transitions',
  '$interval',
  'localStorageService',
  'UtilityService',
  'PermissionService',
  'SystemService',
  'UserService',
  'TokenService',
  'RoleService',
  'EventService',
  'GardenService',
];

/**
 * appRun - Runs the front-end application.
 * @param  {Object} $rootScope           Angular's $rootScope object.
 * @param  {Object} $state               Angular's $state object.
 * @param  {Object} $stateParams         Angular's $stateParams object.
 * @param  {Object} $http                Angular's $http object.
 * @param  {Object} $location            Angular's $location object.
 * @param  {Object} $q                   Angular's $q object.
 * @param  {Object} $uibModal            Angular UI's $uibModal object.
 * @param  {Object} $transitions         Angular's $transitions object.
 * @param  {Object} $interval            Angular's $interval object.
 * @param  {Object} localStorageService  Storage service
 * @param  {Object} UtilityService       Service for configuration/icons.
 * @param  {Object} PermissionService    Service for filtering user accesses.
 * @param  {Object} SystemService        Service for System information.
 * @param  {Object} UserService          Service for User information.
 * @param  {Object} TokenService         Service for Token information.
 * @param  {Object} RoleService          Service for Role information.
 * @param  {Object} EventService         Service for Event information.
 * @param  {Object} GardenService        Service for Garden information.
 */
export default function appRun(
    $rootScope,
    $state,
    $stateParams,
    $http,
    $location,
    $q,
    $uibModal,
    $transitions,
    $interval,
    localStorageService,
    UtilityService,
    PermissionService,
    SystemService,
    UserService,
    TokenService,
    RoleService,
    EventService,
    GardenService,
) {
  $rootScope.$state = $state;
  $rootScope.$stateParams = $stateParams;

  if ($location.search()['showNav'] == 'false'){
    $rootScope.showNav = false;
  } else {
    $rootScope.showNav = true;
  }

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
  $rootScope.hasPermission = PermissionService.hasPermission;

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


  $rootScope.hasGardenPermission = function(permission, garden, global = false) {
    if (!$rootScope.config.authEnabled) return true;
    return $rootScope.hasPermission(permission, global = global, garden_name = garden.name)
  };

  $rootScope.hasSystemPermission = function(permission, system, global = false) {
    if (!$rootScope.config.authEnabled) return true;
    garden_name = PermissionService.findGardenScope(namespace = system.namespace, system_name = system.name, system_version = system.version)
    return $rootScope.hasPermission(permission, global = global, garden_name=garden_name, namespace = system.namespace, system_name = system.name, system_version = system.version)
  };

  $rootScope.hasInstancePermission = function(permission, system, instance, global = false) {
    if (!$rootScope.config.authEnabled) return true;
    garden_name = PermissionService.findGardenScope(namespace = system.namespace, system_name = system.name, system_version = system.version)
    return $rootScope.hasPermission(permission, global = global, garden_name=garden_name, namespace = system.namespace, system_name = system.name, system_version = system.version, instance_name = instance.name)
  };

  $rootScope.hasCommandPermission = function(permission, command, global = false) {
    // Uses the command object generated by command_index controller, not command model
    if (!$rootScope.config.authEnabled) return true;
    garden_name = PermissionService.findGardenScope(namespace = command.namespace, system_name = command.system, system_version = command.version)
    return $rootScope.hasPermission(permission, global = global, garden_name=garden_name, namespace = command.namespace, system_name = command.system, system_version = command.version, command = command.name)
  };

  $rootScope.hasRequestPermission = function(permission, request, global = false) {
    if (!$rootScope.config.authEnabled) return true;
    garden_name = PermissionService.findGardenScope(namespace = request.namespace, system_name = request.system, system_version = request.system_version)

    return $rootScope.hasPermission(permission, global = global, garden_name=garden_name, namespace = request.namespace, system_name = request.system, system_version = request.system_version, instance_name = request.instance_name, command = request.command)
  };

  $rootScope.hasJobPermission = function(permission, job, global = false) {
    if (!$rootScope.config.authEnabled) return true;
    return $rootScope.hasRequestPermission(permission, job.request_template, global=global);
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

  $rootScope.getLocalGarden = function (callback) {
    if ($rootScope.garden !== undefined) {
      return callback();
    }

    if ($rootScope.config.gardenName === undefined) {
      UtilityService.getConfig().then((response) => {
        angular.extend($rootScope.config, camelCaseKeys(response.data));
        return $rootScope.getLocalGarden(callback);
      });
    } else {

      GardenService.getGarden($rootScope.config.gardenName).then((response) => {
        $rootScope.garden = response.data;
        $rootScope.gardensResponse = response;
        return callback();
      },
        (response) => {
          $rootScope.gardenResponse = response;
          $rootScope.garden = {};
        });
    }
  }

  $rootScope.getSystems = function () {
    if ($rootScope.garden === undefined) {
      return $rootScope.getLocalGarden($rootScope.getSystems);
    } else {
      $rootScope.systems = $rootScope.extractSystems($rootScope.garden);
      return $rootScope.systems;
    }
  }

  $rootScope.extractSystems = function(garden, hideRunners = false){
    let systems = [];
    if (garden.systems !== undefined){
      for (let i = 0; i < garden.systems.length; i++){
        if (hideRunners){
          systems.push(hideSystemRunners(garden.systems[i]))
        } else {
          systems.push(garden.systems[i])
        }
      }
      
      systems = garden.systems;
    }
    if (garden.children !== undefined) {
      for (let i = 0; i < garden.children.length; i++){
        systems = systems.concat($rootScope.extractSystems(garden.children[i], true));
      }
    }
    return systems;
  }

  $rootScope.isSystemRoutable = function(system){
    // Check Local First
    for (let i = 0; i < $rootScope.garden.systems.length; i++){
      if (system.id == $rootScope.garden.systems[i].id){
        return true;
      }
    }
    // Check children
    for (let i = 0; i < $rootScope.garden.children.length; i++){
      if ($rootScope.isRemoteSystemRoutable(system, $rootScope.garden.children[i])){
        return true;
      }
    }
    return false;
  }

  $rootScope.isRemoteSystemRoutable = function(system, garden){
    let routable = false;
    for (let i = 0; i < garden.publishing_connections.length; i++){
      if (["PUBLISHING","UNREACHABLE","UNRESPONSIVE","ERROR","UNKNOWN"].includes(garden.publishing_connections[i].status)){
        routable = true;
      }
    }

    if (!routable){
      return false;
    }
    for (let i = 0; i < garden.systems.length; i++){
      if (system.id == garden.systems[i].id){
        return true;
      }
    }

    for (let i = 0; i < garden.children.length; i++){
      if ($rootScope.isRemoteSystemRoutable(system, garden.children[i])){
        return true;
      }
    }

    return false;
  }

  $rootScope.extractGardenChildren = function(gardens) {
    let results = []
    for (let i = 0; i < gardens.length; i++){
      if (gardens[i]["connection_type"] == "LOCAL"){
        results.push(gardens[i]);
        $rootScope.extractGardenChildrenLoop(results, gardens[i], true);
      }
    }
    return results;
  }

  $rootScope.extractGardenChildrenLoop = function(gardens, garden, include_systems) {
    for (let i = 0; i < garden.children.length; i++){
      gardens.push(garden.children[i]);
      $rootScope.extractGardenChildrenLoop(gardens, garden.children[i], true);
    }
    return gardens;
  }

  function upsertGardenSystems(garden, seenIndexes, hideRunners = false){
    let routable = (garden.connection_type == "LOCAL");
    for (let i = 0; i < garden.publishing_connections.length; i++){
      if (["PUBLISHING","UNREACHABLE","UNRESPONSIVE","ERROR","UNKNOWN"].includes(garden.publishing_connections[i].status)){
        routable = true;
      }
    }
    if (routable) {
      if (garden.systems !== undefined) {
        for (let i = 0; i < garden.systems.length; i++){
          seenIndexes.push(upsertSystem(garden.systems[i], hideRunners));
        }
      }
      for (let i = 0; i < garden.children.length; i++){
        upsertGardenSystems(garden.children[i], seenIndexes, true);
      }
    }
  }

  function updateGardenSystems(){
    if ($rootScope.garden !== undefined) {
      let seenIndexes = [];
      upsertGardenSystems($rootScope.garden, seenIndexes);
      // Loop through seen indexes and remove everything not seen starting at the end
      for (let i = ($rootScope.systems.length - 1); i > -1; i--){
        if (!seenIndexes.includes(i)){
          $rootScope.systems.splice(i, 1);
        }
      }
    }
    $rootScope.systems;
  }

  function hideSystemRunners(system) {
    for (let i = 0; i < system.instances.length; i++){
      if (system.instances[i].metadata.runner_id !== undefined){
        delete system.instances[i].metadata.runner_id
      }
    }
    return system
  }

  function upsertSystem(system, hideRunner = false) {
    const index = _.findIndex($rootScope.systems, {id: system.id});

    if (hideRunner){
      system = hideSystemRunners(system)
    }
    if (index == -1) {
      $rootScope.systems.push(system);
      return $rootScope.systems.length - 1;
    } else {
      $rootScope.systems.splice(index, 1, system);
      return index;
    }
  }

  function updateGardenChildren(srcGarden, newGarden) {

    let matched = false;
    for (let i = 0; i < srcGarden.children.length; i++){
      if (srcGarden.children[i].name== newGarden.name){
        srcGarden.children[i] = newGarden;
        matched = true;
        break
      }
    }
    if (!matched){
      for (let i = 0; i < srcGarden.children.length; i++){
        srcGarden.children[i] = updateGardenChildren(srcGarden.children[i], newGarden);
      }
    }
    
    return srcGarden;
  }

  EventService.addCallback('global_systems', (event) => {
    if ($rootScope.garden !== undefined && event.garden == $rootScope.garden.name && event.name == "GARDEN_UPDATED"){
      if ($rootScope.garden.name== event.payload.name){
        $rootScope.garden = event.payload;
      } else {
        $rootScope.garden = updateGardenChildren($rootScope.garden, event.payload);
      }
      updateGardenSystems();
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
