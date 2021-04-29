
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
    .state('base.about', {
      url: 'about',
      templateUrl: 'about.html',
      controller: 'AboutController',
    })
    .state('login', {
      templateUrl: 'login.html',
      controller: 'LoginController',
    })
    .state('base.systems', {
      url: 'systems/',
      templateUrl: 'system_index.html',
      controller: 'SystemIndexController',
    })
    .state('base.system', {
      url: 'systems/:namespace/:systemName/:systemVersion',
      templateUrl: 'command_index.html',
      controller: 'CommandIndexController',
      resolve: {
        system: ['$stateParams', 'SystemService', ($stateParams, SystemService) => {
          return SystemService.findSystem(
            $stateParams.namespace, $stateParams.systemName, $stateParams.systemVersion
          ) || {};
        }],
      },
    })
    .state('base.systemNs', {
      url: 'systems/:namespace',
      templateUrl: 'command_index.html',
      controller: 'CommandIndexController',
      resolve: {
        system: ['$stateParams', 'SystemService', ($stateParams, SystemService) => {
          return SystemService.findSystem($stateParams.namespace) || {};
        }],
      },
    })
    .state('base.systemName', {
      url: 'systems/:namespace/:systemName',
      templateUrl: 'command_index.html',
      controller: 'CommandIndexController',
      resolve: {
        system: ['$stateParams', 'SystemService', ($stateParams, SystemService) => {
          return SystemService.findSystem(
            $stateParams.namespace, $stateParams.systemName
          ) || {};
        }],
      },
    })
    .state('base.commands', {
      url: 'commands/',
      templateUrl: 'command_index.html',
      controller: 'CommandIndexController',
    })
    // Don't ask me why this can't be nested as base.system.command
    // Think it's something to do with nested views... I think maybe because
    // base.system defines a template
    .state('base.command', {
      url: 'systems/:namespace/:systemName/:systemVersion/commands/:commandName/',
      templateUrl: 'command_view.html',
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
      templateUrl: 'job_index.html',
      controller: 'JobIndexController',
    })
    .state('base.jobscreatesystem', {
      url: 'jobs/create/system/',
      templateUrl: 'job/create_system.html',
      controller: 'JobCreateSystemController',
    })
    .state('base.jobscreatecommand', {
      url: 'jobs/create/command/',
      templateUrl: 'job/create_command.html',
      controller: 'JobCreateCommandController',
      params: {
        'system': null,
      },
    })
    .state('base.jobscreaterequest', {
      url: 'jobs/create/request/',
      templateUrl: 'job/create_request.html',
      controller: 'JobCreateRequestController',
      params: {
        'system': null,
        'command': null,
        'job': null,
      },
    })
    .state('base.jobscreatetrigger', {
      url: 'jobs/create/trigger/',
      templateUrl: 'job/create_trigger.html',
      controller: 'JobCreateTriggerController',
      params: {
        'request': null,
        'job': null,
      },
    })
    .state('base.job', {
      'url': 'jobs/:id/',
      'templateUrl': 'job_view.html',
      'controller': 'JobViewController',
    })
    .state('base.requests', {
      url: 'requests/',
      templateUrl: 'request_index.html',
      controller: 'RequestIndexController',
    })
    .state('base.request', {
      url: 'requests/:requestId/',
      templateUrl: 'request_view.html',
      controller: 'RequestViewController',
    })
    .state('base.queues', {
      url: 'admin/queues/',
      templateUrl: 'admin_queue.html',
      controller: 'AdminQueueController',
    })
    .state('base.system_admin', {
      url: 'admin/systems/',
      templateUrl: 'admin_system.html',
      controller: 'AdminSystemController',
    })
    .state('base.garden_admin', {
      url: 'admin/gardens/',
      templateUrl: 'admin_garden_index.html',
      controller: 'AdminGardenController',
    })
    .state('base.garden_view', {
      url: 'admin/gardens/:name/',
      templateUrl: 'admin_garden_view.html',
      controller: 'AdminGardenViewController',
    })
    .state('base.user_admin', {
      url: 'admin/users/',
      templateUrl: 'admin_user.html',
      controller: 'AdminUserController',
    })
    .state('base.role_admin', {
      url: 'admin/roles/',
      templateUrl: 'admin_role.html',
      controller: 'AdminRoleController',
    });
};
