jobCreateCommandController.$inject = ["$scope", "$stateParams"];

/**
 * jobCreateController - Controller for the job create page.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $stateParams      Angular's $stateParams object.
 */
export default function jobCreateCommandController($scope, $stateParams) {
  $scope.setWindowTitle("scheduler");

  $scope.system = $stateParams.system;
}
