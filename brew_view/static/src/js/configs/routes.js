
routeConfig.$inject = ['$stateProvider', '$urlRouterProvider'];

/**
 * routeConfig - routing config for the application.
 * @param  {type} $stateProvider     Angular's $stateProvider object.
 * @param  {type} $urlRouterProvider Angular's $urlRouterProvider object.
 */
export default function routeConfig($stateProvider, $urlRouterProvider) {
  const basePath = 'partials/';

  $urlRouterProvider.otherwise('/');

  $stateProvider
    .state('landing', {
        url: '/',
        templateUrl: basePath + 'landing.html',
        controller: 'LandingController',
    })
    .state('login', {
      url: '/login',
      templateUrl: basePath + 'login.html',
      controller: 'LoginController',
    })
    // Unused by our UI, but helpful for external links.
    .state('systemID', {
      url: '/systems/:id',
      templateUrl: basePath + 'system_view.html',
      controller: 'SystemViewController',
    })
    .state('system', {
      'url': '/systems/:name/:version',
      'templateUrl': basePath + 'system_view.html',
      'controller': 'SystemViewController',
    })
    .state('about', {
      url: '/about',
      templateUrl: basePath + 'about.html',
      controller: 'AboutController',
    })
    .state('queues', {
      url: '/admin/queues',
      templateUrl: basePath + 'admin_queue.html',
      controller: 'QueueIndexController',
    })
    .state('commands', {
      url: '/commands',
      templateUrl: basePath + 'command_index.html',
      controller: 'CommandIndexController',
    })
    .state('command', {
      url: '/systems/:systemName/:systemVersion/commands/:name',
      templateUrl: basePath + 'command_view.html',
      controller: 'CommandViewController',
      params: {
        request: null,
        id: null,
      },
    })
    // Unused by our UI, but helpful for external links.
    .state('commandID', {
      url: '/commands/:command_id',
      templateUrl: basePath + 'command_view.html',
      controller: 'CommandViewController',
      params: {
        request: null,
      },
    })
    .state('requests', {
      url: '/requests',
      templateUrl: basePath + 'request_index.html',
      controller: 'RequestIndexController',
    })
    .state('request', {
      url: '/requests/:request_id',
      templateUrl: basePath + 'request_view.html',
      controller: 'RequestViewController',
    })
    .state('system_admin', {
      url: '/admin/systems',
      templateUrl: basePath + 'admin_system.html',
      controller: 'SystemAdminController',
    });
};
