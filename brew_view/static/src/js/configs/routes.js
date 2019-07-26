
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
    .state('login', {
      url: '/login',
      templateUrl: basePath + 'login.html',
      controller: 'LoginController',
    })
    .state('base.namespace.systems', {
      url: '/systems',
      templateUrl: basePath + 'system_index.html',
      controller: 'SystemIndexController',
    })
    .state('base.namespace.systemID', {
      url: '/systems/:id',
      controller: ($state, $stateParams, SystemService) => {
        let sys = SystemService.findSystemByID($stateParams.id);
        $state.go('base.namespace.system', {name: sys.name, version: sys.version});
      },
    })
    .state('base.namespace.system', {
      url: '/systems/:name/:version',
      templateUrl: basePath + 'system_view.html',
      controller: 'SystemViewController',
      resolve:{
        system: ($stateParams, SystemService) => {
          let sys = SystemService.findSystem($stateParams.name, $stateParams.version);
          return SystemService.getSystem(sys.id);
        },
      },
    })
    .state('base.namespace.about', {
      url: '/about',
      templateUrl: basePath + 'about.html',
      controller: 'AboutController',
    })
    .state('base.namespace.jobs', {
      url: '/jobs',
      templateUrl: basePath + 'job_index.html',
      controller: 'JobIndexController',
    })
    .state('base.namespace.jobsCreate', {
      url: '/jobs/create',
      templateUrl: basePath + 'job_create.html',
      controller: 'JobCreateController',
      params: {
        'request': null,
        'system': null,
        'command': null,
      },
    })
    .state('base.namespace.job', {
      'url': '/jobs/:id',
      'templateUrl': basePath + 'job_view.html',
      'controller': 'JobViewController',
    })
    .state('base.namespace.commands', {
      url: '/commands',
      templateUrl: basePath + 'command_index.html',
      controller: 'CommandIndexController',
    })
    .state('base.namespace.command', {
      url: '/systems/:systemName/:systemVersion/commands/:name',
      templateUrl: basePath + 'command_view.html',
      controller: 'CommandViewController',
      params: {
        request: null,
        id: null,
      },
    })
    // Unused by our UI, but helpful for external links.
    .state('base.namespace.commandID', {
      url: '/commands/:id',
      templateUrl: basePath + 'command_view.html',
      controller: 'CommandViewController',
      params: {
        request: null,
      },
    })
    .state('base.namespace.requests', {
      url: '/requests',
      templateUrl: basePath + 'request_index.html',
      controller: 'RequestIndexController',
    })
    .state('base.namespace.request', {
      url: '/requests/:request_id',
      templateUrl: basePath + 'request_view.html',
      controller: 'RequestViewController',
    })
    .state('base.namespace.queues', {
      url: '/admin/queues',
      templateUrl: basePath + 'admin_queue.html',
      controller: 'AdminQueueController',
    })
    .state('base.namespace.system_admin', {
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
