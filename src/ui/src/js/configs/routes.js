
import {camelCaseKeys} from '../services/utility_service.js';

routeConfig.$inject = [
  '$stateProvider',
  '$urlRouterProvider',
  '$urlMatcherFactoryProvider',
  '$locationProvider',
];

/**
 * routeConfig - routing config for the application.
 * @param  {Object} $stateProvider              Angular's $stateProvider object.
 * @param  {Object} $urlRouterProvider          Angular's $urlRouterProvider object.
 * @param  {Object} $urlMatcherFactoryProvider  Angular's $urlMatcherFactoryProvider object.
 * @param  {Object} $locationProvider           Angular's $locationProvider object.
 */
export default function routeConfig(
    $stateProvider,
    $urlRouterProvider,
    $urlMatcherFactoryProvider,
    $locationProvider) {
  const basePath = 'partials/';

  $urlRouterProvider.otherwise('/');
  $urlMatcherFactoryProvider.strictMode(false);

  // // use the HTML5 History API
  // $locationProvider.html5Mode(true);

  $stateProvider
    .state('base', {
      url: '/',
      resolve: {
        config: ['$rootScope', 'UtilityService', ($rootScope, UtilityService) => {
          return UtilityService.getConfig().then(
            (response) => {
              angular.extend($rootScope.config, camelCaseKeys(response.data));
            }
          );
        }],
        namespaces: ['$rootScope', 'UtilityService', ($rootScope, UtilityService) => {
          return UtilityService.getNamespaces().then(
            (response) => {
              $rootScope.namespaces = response.data;
            }
          );
        }],
      },
    })
    .state('base.landing', {
      templateUrl: basePath + 'landing.html',
    })
    .state('base.about', {
      url: 'about',
      templateUrl: basePath + 'about.html',
      controller: 'AboutController',
    })
    .state('base.namespace', {
      url: ':namespace/',
      resolve: {
        systems: [
        '$stateParams', '$rootScope', 'SystemService',
        ($stateParams, $rootScope, SystemService) => {
          return SystemService.getSystems(
            {
              dereferenceNested: false,
              includeFields: 'id,name,version,description,instances,commands',
              namespace: $stateParams.namespace,
            },
          ).then(
            (response) => {
              $rootScope.sysResponse = response;
              $rootScope.systems = response.data;
            },
            (response) => {
              $rootScope.sysResponse = response;
              $rootScope.systems = [];
            }
          );
        }],
      },
    })
    .state('login', {
      templateUrl: basePath + 'login.html',
      controller: 'LoginController',
    })
    .state('base.namespace.systems', {
      url: 'systems/',
      templateUrl: basePath + 'system_index.html',
      controller: 'SystemIndexController',
    })
    .state('base.namespace.systemID', {
      url: 'systems/:id/',
      controller: ['$state', '$stateParams', 'SystemService', ($state, $stateParams, SystemService) => {
        let sys = SystemService.findSystemByID($stateParams.id);
        $state.go('base.namespace.system', {name: sys.name, version: sys.version});
      }],
    })
    .state('base.namespace.system', {
      url: 'systems/:systemName/:systemVersion/',
      templateUrl: basePath + 'system_view.html',
      controller: 'SystemViewController',
      resolve: {
        system: ['$stateParams', 'SystemService', ($stateParams, SystemService) => {
          let sys = SystemService.findSystem($stateParams.systemName, $stateParams.systemVersion) || {};
          return SystemService.getSystem(sys.id).catch(
            (response) => response
          );
        }],
      },
    })
    // Don't ask me why this can't be nested as base.namespace.system.command
    // Think it's something to do with nested views... I think maybe because
    // base.namespace.system defines a template
    .state('base.namespace.command', {
      url: 'systems/:systemName/:systemVersion/commands/:commandName/',
      templateUrl: basePath + 'command_view.html',
      controller: 'CommandViewController',
      params: {
        request: null,
        id: null,
      },
      resolve: {
        system: ['$stateParams', 'SystemService', ($stateParams, SystemService) => {
          let sys = SystemService.findSystem($stateParams.systemName, $stateParams.systemVersion) || {};
          return SystemService.getSystem(sys.id).catch(
            (response) => response
          );
        }],
        command: ['$stateParams', 'CommandService', 'system', ($stateParams, CommandService, system) => {
          let cmd = _.find(system.data.commands, {name: $stateParams.commandName});
          // if (_.isUndefined(cmd)) {
          //   return $q.reject({status: 404, data: {message: 'No matching command'}});
          // }

          // We already have the command the system, but this is better as it
          // validates that user has bg-command-read
          return CommandService.getCommand(cmd.id).catch(
            (response) => response
          );
        }],
      },
    })
    .state('base.namespace.jobs', {
      url: 'jobs/',
      templateUrl: basePath + 'job_index.html',
      controller: 'JobIndexController',
    })
    .state('base.namespace.jobsCreate', {
      url: 'jobs/create/',
      templateUrl: basePath + 'job_create.html',
      controller: 'JobCreateController',
      params: {
        'request': null,
        'system': null,
        'command': null,
      },
    })
    .state('base.namespace.job', {
      'url': 'jobs/:id/',
      'templateUrl': basePath + 'job_view.html',
      'controller': 'JobViewController',
    })
    .state('base.namespace.commands', {
      url: 'commands/',
      templateUrl: basePath + 'command_index.html',
      controller: 'CommandIndexController',
      resolve: {
        detailSystems: ['$stateParams', 'SystemService', ($stateParams, SystemService) => {
          return SystemService.getSystems(
            {namespace: $stateParams.namespace}
          ).catch(
            (response) => response
          );
        }],
        commands: ['$stateParams', 'CommandService', ($stateParams, CommandService) => {
          return CommandService.getCommands(
            {namespace: $stateParams.namespace}
          ).catch(
            (response) => response
          );
        }],
      },
    })
    // .state('base.namespace.commandID', {
    //   url: '^/commands/:commandId',
    //   templateUrl: basePath + 'command_view.html',
    //   controller: 'CommandViewController',
    //   params: {
    //     request: null,
    //   },
    //   systems: (SystemService) => {
    //     return SystemService.getSystems();
    //   },
    //   controller: ($state, $stateParams, CommandService, systems) => {
    //     let sys = SystemService.findSystemByID($stateParams.id);
    //     $state.go('base.namespace.system', {name: sys.name, version: sys.version});
    //   },
    // })
    .state('base.namespace.requests', {
      url: 'requests/',
      templateUrl: basePath + 'request_index.html',
      controller: 'RequestIndexController',
    })
    .state('base.namespace.request', {
      url: 'requests/:requestId/',
      templateUrl: basePath + 'request_view.html',
      controller: 'RequestViewController',
      resolve: {
        request: ['$stateParams', 'RequestService', ($stateParams, RequestService) => {
          return RequestService.getRequest($stateParams.requestId).catch(
            (response) => response
          );
        }],
      },
    })
    .state('base.namespace.queues', {
      url: 'admin/queues/',
      templateUrl: basePath + 'admin_queue.html',
      controller: 'AdminQueueController',
    })
    .state('base.namespace.system_admin', {
      url: 'admin/systems/',
      templateUrl: basePath + 'admin_system.html',
      controller: 'AdminSystemController',
    })
    .state('base.garden_admin', {
      url: 'admin/gardens/',
      templateUrl: basePath + 'admin_garden_index.html',
      controller: 'AdminGardenController',
    })
    .state('base.garden_admin.garden', {
      url: ':name/',
      templateUrl: basePath + 'admin_garden_view.html',
      controller: 'AdminGardenViewController',
    })
    .state('base.user_admin', {
      url: 'admin/users/',
      templateUrl: basePath + 'admin_user.html',
      controller: 'AdminUserController',
    })
    .state('base.role_admin', {
      url: 'admin/roles/',
      templateUrl: basePath + 'admin_role.html',
      controller: 'AdminRoleController',
    });
};
