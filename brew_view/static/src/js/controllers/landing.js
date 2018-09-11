
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
  $scope.setWindowTitle();

  $scope.util = UtilityService;

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  $scope.exploreSystem = function(system) {
    $location.path($rootScope.getSystemUrl(system.id));
  };

  function loadSystems() {
    $scope.response = undefined;
    $scope.data = {};

    SystemService.getSystems(false).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  }

  $scope.$on('userChange', () => {
    loadSystems();
  });

  // We need to reload the root-level systems list here as well, otherwise
  // new systems won't show up in the sidebar or link correctly
  // We only need to do this on initial controller load since the root-level
  // systems will be reloaded as part of the user change process already
  $rootScope.loadSystems();

  loadSystems();
};
