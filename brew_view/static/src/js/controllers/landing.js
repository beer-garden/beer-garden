
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
    loading: true,
    error: false,
    errorMessage: '',
    status: null,
  };

  $scope.successCallback = function(response) {
    $rootScope.systems = response.data;
    $scope.systems.data = response.data;
    $scope.systems.loaded = true;
    $scope.systems.loading = false;
    $scope.systems.error = false;
    $scope.systems.status = response.status;
    $scope.systems.errorMessage = '';
  };

  $scope.failureCallback = function(response) {
    $scope.systems.data = [];
    $scope.systems.loaded = false;
    $scope.systems.loading = false;
    $scope.systems.error = true;
    $scope.systems.status = response.status;
    $scope.systems.errorMessage = response.data.message;
  };

  $scope.exploreSystem = function(system) {
    $location.path($rootScope.getSystemUrl(system.id));
  };

  function loadSystems() {
    $scope.systems.loading = true;

    SystemService.getSystems(false).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  }

  $scope.$on('userChange', () => {
    loadSystems();
  });

  loadSystems();
};
