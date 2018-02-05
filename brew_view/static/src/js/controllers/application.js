applicationController.$inject = ['$scope', 'UtilityService'];
export default function applicationController($scope, UtilityService) {
  $scope.getIcon = UtilityService.getIcon;
};
