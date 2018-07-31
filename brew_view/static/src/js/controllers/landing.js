
landingController.$inject = [
  '$scope',
  '$rootScope',
  '$location',
  '$interval',
  'SystemService',
  'UtilityService',
];

/**
 * landingController - Controller for the landing page.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {$rootScope} $rootScope Angular's $rootScope object.
 * @param  {$location} $location   Angular's $location object.
 * @param  {$interval} $interval   Angular's $interval object.
 * @param  {Object} SystemService  Beer-Garden's sytem service.
 * @param  {Object} UtilityService Beer-Garden's utility service.
 */
export default function landingController(
  $scope,
  $rootScope,
  $location,
  $interval,
  SystemService,
  UtilityService) {
  $scope.util = UtilityService;

  $scope.systems = {
    data: [],
    loaded: false,
    error: false,
    errorMessage: '',
    status: null,
    errorMap: {
      'empty': {
        'solutions': [
          {
            problem: 'Backend Down',
            description: 'If the backend is down, there will be no systems to control',
            resolution: '<kbd>service bartender start</kbd>',
          },
          {
            problem: 'Plugin Problems',
            description: 'If Plugins attempted to start, but are failing to startup, then ' +
                         'you\'ll have to contact the plugin maintainer. You can tell what\'s ' +
                         ' wrong by their logs. Plugins are located at ' +
                         '<code>$APP_HOME/plugins</code>',
            resolution: '<kbd>less $APP_HOME/log/my-plugin.log</kbd>',
          },
          {
            problem: 'Database Names Do Not Match',
            description: 'It is possible that the backend is pointing to a Different Database ' +
                         'than the Frontend. Check to make sure that the <code>DB_NAME</code> ' +
                         'in both config files is the same',
            resolution: '<kbd>vim $APP_HOME/conf/bartender.json</kbd><br />' +
                        '<kbd>vim $APP_HOME/conf/brew-view.json</kbd>',
          },
          {
            problem: 'There Are No Systems',
            description: 'If no one has ever developed any plugins, then there will be no ' +
                         'systems here. You\'ll need to build your own plugins.',
            resolution: 'Develop a Plugin',
          },
        ],
      },
    },
  };

  $scope.successCallback = function(response) {
    $rootScope.systems = response.data;
    $scope.systems.data = response.data;
    $scope.systems.loaded = true;
    $scope.systems.error = false;
    $scope.systems.status = response.status;
    $scope.systems.errorMessage = '';
  };

  $scope.failureCallback = function(response) {
    $scope.systems.data = [];
    $scope.systems.loaded = false;
    $scope.systems.error = true;
    $scope.systems.status = response.status;
    $scope.systems.errorMessage = response.data.message;
  };

  $scope.exploreSystem = function(system) {
    $location.path($rootScope.getSystemUrl(system.id));
  };

  function loadSystems() {
    SystemService.getSystems(false)
      .then($scope.successCallback, $scope.failureCallback);
  }

  $scope.$on('userChange', () => {
    loadSystems();
  });

  loadSystems();
};
