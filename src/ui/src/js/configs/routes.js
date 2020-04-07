
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
        systems: [ '$rootScope', 'SystemService', ($rootScope, SystemService) => {
          return SystemService.getSystems().then(
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
    .state('base.landing', {
      templateUrl: basePath + 'landing.html',
    })
    .state('base.about', {
      url: 'about',
      templateUrl: basePath + 'about.html',
      controller: 'AboutController',
    })
    .state('login', {
      templateUrl: basePath + 'login.html',
      controller: 'LoginController',
    })
    .state('base.systems', {
      url: 'systems/',
      templateUrl: basePath + 'system_index.html',
      controller: 'SystemIndexController',
    })
    .state('base.systemID', {
      url: 'systems/:id/',
      controller: ['$state', '$stateParams', 'SystemService', ($state, $stateParams, SystemService) => {
        let sys = SystemService.findSystemByID($stateParams.id);
        $state.go('base.system', {namespace: sys.namespace, systemName: sys.name, systemVersion: sys.version});
      }],
    })
    .state('base.system', {
      url: 'commands?namespace&systemName&systemVersion',
      templateUrl: basePath + 'command_index.html',
      controller: 'CommandIndexController',
      resolve: {
        system: ['$stateParams', 'SystemService', ($stateParams, SystemService) => {
          let sys = SystemService.findSystem(
            $stateParams.namespace, $stateParams.systemName, $stateParams.systemVersion
          ) || {};
          return SystemService.getSystem(sys.id).catch(
            (response) => response
          );
        }],
      },
    })
    .state('base.commands', {
      url: 'commands/',
      templateUrl: basePath + 'command_index.html',
      controller: 'CommandIndexController',
    })
    .state('base.commandID', {
      url: 'commands/:id/',
      controller: ['$state', '$stateParams', 'CommandService', 'SystemService',
          ($state, $stateParams, CommandService, SystemService) => {
        let command = CommandService.findCommandByID($stateParams.id);
        let system = SystemService.findSystemByID(command.system.id);

        $state.go('base.command', {
          namespace: system.namespace,
          systemName: system.name,
          systemVersion: system.version,
          commandName: command.name,
        });
      }],
    })
    // Don't ask me why this can't be nested as base.system.command
    // Think it's something to do with nested views... I think maybe because
    // base.system defines a template
    .state('base.command', {
      url: 'systems/:namespace/:systemName/:systemVersion/commands/:commandName/',
      templateUrl: basePath + 'command_view.html',
      controller: 'CommandViewController',
      params: {
        request: null,
        id: null,
      },
      resolve: {
        system: ['$stateParams', 'SystemService', ($stateParams, SystemService) => {
          return SystemService.findSystem(
            $stateParams.namespace, $stateParams.systemName, $stateParams.systemVersion
          );
        }],
        command: ['$stateParams', 'system', ($stateParams, system) => {
          return _.find(system.commands, {name: $stateParams.commandName});
        }],
      },
    })
    .state('base.jobs', {
      url: 'jobs/',
      templateUrl: basePath + 'job_index.html',
      controller: 'JobIndexController',
    })
    .state('base.jobsCreate', {
      url: 'jobs/create/',
      templateUrl: basePath + 'job_create.html',
      controller: 'JobCreateController',
      params: {
        'request': null,
        'system': null,
        'command': null,
      },
    })
    .state('base.job', {
      'url': 'jobs/:id/',
      'templateUrl': basePath + 'job_view.html',
      'controller': 'JobViewController',
    })
    .state('base.requests', {
      url: 'requests/',
      templateUrl: basePath + 'request_index.html',
      controller: 'RequestIndexController',
    })
    .state('base.request', {
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
    .state('base.queues', {
      url: 'admin/queues/',
      templateUrl: basePath + 'admin_queue.html',
      controller: 'AdminQueueController',
    })
    .state('base.system_admin', {
      url: 'admin/systems/',
      templateUrl: basePath + 'admin_system.html',
      controller: 'AdminSystemController',
    })
    .state('base.garden_admin', {
      url: 'admin/gardens/',
      templateUrl: basePath + 'admin_garden_index.html',
      controller: 'AdminGardenController',
    })
    .state('base.garden_view', {
      url: 'admin/gardens/:name/',
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
