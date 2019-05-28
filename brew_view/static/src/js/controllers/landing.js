
landingController.$inject = [
  '$scope',
  '$rootScope',
  '$state',
  '$stateParams',
  'SystemService',
  'UtilityService',
];

/**
 * landingController - Controller for the landing page.
 * @param  {Object} $scope         Angular's $scope object.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {Object} $state         Angular's $state object.
 * @param  {Object} $stateParams   Angular's $stateParams object.
 * @param  {Object} SystemService  Beer-Garden's sytem service.
 * @param  {Object} UtilityService Beer-Garden's utility service.
 */
export default function landingController(
    $scope,
    $rootScope,
    $state,
    $stateParams,
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
    $state.go('namespace.system',
      {
        'name': system.name,
        'version': system.version,
      }
    );
  };

  function loadSystems() {
    $scope.response = undefined;
    $scope.data = {};

    SystemService.getSystems($stateParams.namespace, false).then(
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
