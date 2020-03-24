
systemIndexController.$inject = [
  '$scope',
  '$rootScope',
  '$state',
  '$stateParams',
  '$sce',
  'SystemService',
  'UtilityService',
];

/**
 * systemIndexController - Controller for the system index page.
 * @param  {Object} $scope         Angular's $scope object.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {Object} $state         Angular's $state object.
 * @param  {Object} SystemService  Beer-Garden's sytem service.
 * @param  {Object} UtilityService Beer-Garden's utility service.
 */
export default function systemIndexController(
    $scope,
    $rootScope,
    $state,
    $stateParams,
    $sce,
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
    $state.go('base.system',
      {
        'systemName': system.name,
        'systemVersion': system.version,
        'namespace': system.namespace,
      }
    );
  };

  $scope.buildBreadCrumbs = function() {

    var dirDisplay =  [".."];

    if ('namespace' in $stateParams){
        dirDisplay.push($stateParams.namespace);

        if ('system' in $stateParams){
          dirDisplay.push($stateParams.system);
        }
    }

    $scope.breadCrumbs = dirDisplay;

  }

  $scope.getPageFilter = function (system) {

    if ('namespace' in $stateParams){
        if (system.namespace != $stateParams.namespace){
          return false;
        }
        else if ('system' in $stateParams){
          if (system.name != $stateParams.system){
            return (system.name == $stateParams.system);
          }
        }
      }
    return true;
  }

  $scope.response = $rootScope.sysResponse;
  $scope.data = $rootScope.systems;
};
