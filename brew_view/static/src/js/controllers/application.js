applicationController.$inject = ['$scope', 'UtilityService'];

/**
 * applicationController - Base Application controller.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {Object} UtilityService Beer-Garden's Utility Service.
 */
export default function applicationController($scope, UtilityService) {
  $scope.getIcon = UtilityService.getIcon;
};
