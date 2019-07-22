applicationController.$inject = ['$scope', 'SystemService', 'UtilityService'];

/**
 * applicationController - Base Application controller.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {Object} SystemService  Beer-Garden's System Service.
 * @param  {Object} UtilityService Beer-Garden's Utility Service.
 */
export default function applicationController($scope, SystemService, UtilityService) {
  $scope.getIcon = UtilityService.getIcon;

  $scope.sidebarSystems = [];

  SystemService.subscribe($scope, function newSystems() {
    $scope.sidebarSystems = SystemService.cachedSystems();
  });
};
