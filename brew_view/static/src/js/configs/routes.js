
import {camelCaseKeys} from '../services/utility_service.js';

routeConfig.$inject = ['$stateProvider', '$urlRouterProvider', '$locationProvider'];

/**
 * routeConfig - routing config for the application.
 * @param  {type} $stateProvider     Angular's $stateProvider object.
 * @param  {type} $urlRouterProvider Angular's $urlRouterProvider object.
 * @param  {type} $locationProvider  Angular's $locationProvider object.
 */
export default function routeConfig($stateProvider, $urlRouterProvider, $locationProvider) {
  const basePath = 'partials/';

  $urlRouterProvider.otherwise('/');

  // // use the HTML5 History API
  // $locationProvider.html5Mode(true);

  $stateProvider
    .state('base', {
      url: '/',
      resolve: {
        config: (UtilityService) => {
          return UtilityService.getConfig();
        },
        controller: ($rootScope, $state, config) => {
          angular.extend($rootScope.config, camelCaseKeys(config.data));

          $rootScope.namespaces = _.concat(
            $rootScope.config.namespaces.local,
            $rootScope.config.namespaces.remote,
          );

          if ($rootScope.config.namespaces.local) {
            $state.go(
              'base.namespace.systems',
              {namespace: $rootScope.config.namespaces.local},
            );
          }
        },
      },
    })
    .state('base.namespace', {
      url: ':namespace',
      params: {
        namespace: {
          value: '',
        },
      },
      resolve: {
        systems: ($stateParams, SystemService) => {
          return SystemService.getSystems(
            {
              dereferenceNested: false,
              includeFields: 'id,name,version,description,instances,commands',
            },
            {'bg-namespace': $stateParams.namespace},
          );
        },
      },
      controller: ($rootScope, systems) => {
        $rootScope.sysResponse = systems;
        $rootScope.systems = systems.data;
      },
    })
    .state('base.namespace.systems', {
      url: '/systems',
      templateUrl: basePath + 'system_index.html',
      controller: 'SystemIndexController',
    })
    .state('login', {
      url: '/login',
      templateUrl: basePath + 'login.html',
      controller: 'LoginController',
    })
    // Unused by our UI, but helpful for external links.
    .state('base.namespace.systemID', {
      url: '/systems/:id',
      templateUrl: basePath + 'system_view.html',
      controller: 'SystemViewController',
    })
    .state('base.namespace.system', {
      url: '/systems/:name/:version',
      params: {
        name: {
          value: '',
        },
        version: {
          value: '',
        },
      },
      templateUrl: basePath + 'system_view.html',
      controller: 'SystemViewController',
    })
    .state('namespace.about', {
      url: '/about',
      templateUrl: basePath + 'about.html',
      controller: 'AboutController',
    })
    .state('namespace.jobs', {
      url: '/jobs',
      templateUrl: basePath + 'job_index.html',
      controller: 'JobIndexController',
    })
    .state('namespace.jobsCreate', {
      url: '/jobs/create',
      templateUrl: basePath + 'job_create.html',
      controller: 'JobCreateController',
      params: {
        'request': null,
        'system': null,
        'command': null,
      },
    })
    .state('namespace.job', {
      'url': '/jobs/:id',
      'templateUrl': basePath + 'job_view.html',
      'controller': 'JobViewController',
    })
    .state('namespace.commands', {
      url: '/commands',
      templateUrl: basePath + 'command_index.html',
      controller: 'CommandIndexController',
    })
    .state('namespace.command', {
      url: '/systems/:systemName/:systemVersion/commands/:name',
      templateUrl: basePath + 'command_view.html',
      controller: 'CommandViewController',
      params: {
        request: null,
        id: null,
      },
    })
    // Unused by our UI, but helpful for external links.
    .state('namespace.commandID', {
      url: '/commands/:id',
      templateUrl: basePath + 'command_view.html',
      controller: 'CommandViewController',
      params: {
        request: null,
      },
    })
    .state('namespace.requests', {
      url: '/requests',
      templateUrl: basePath + 'request_index.html',
      controller: 'RequestIndexController',
    })
    .state('namespace.request', {
      url: '/requests/:request_id',
      templateUrl: basePath + 'request_view.html',
      controller: 'RequestViewController',
    })
    .state('namespace.queues', {
      url: '/admin/queues',
      templateUrl: basePath + 'admin_queue.html',
      controller: 'AdminQueueController',
    })
    .state('namespace.system_admin', {
      url: '/admin/systems',
      templateUrl: basePath + 'admin_system.html',
      controller: 'AdminSystemController',
    })
    .state('user_admin', {
      url: '/admin/users',
      templateUrl: basePath + 'admin_user.html',
      controller: 'AdminUserController',
    })
    .state('role_admin', {
      url: '/admin/roles',
      templateUrl: basePath + 'admin_role.html',
      controller: 'AdminRoleController',
    });
};
