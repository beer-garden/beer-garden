adminSystemForceDeleteController.$inject = [
  '$scope',
  '$uibModalInstance',
  'SystemService',
  'system',
  'response',
];

/**
 * adminSystemForceDeleteController - Angular controller for force deleting systems.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $uibModalInstance
 * @param  {Object} SystemService     Beer-Garden's system service object.
 * @param  {Object} system
 * @param  {Object} response
 */
export default function adminSystemForceDeleteController(
    $scope,
    $uibModalInstance,
    SystemService,
    system,
    response,
) {
  $scope.alerts = [];
  $scope.system = system;
  $scope.error = response.data.message;

  $scope.forceDeleteSystem = function(system) {
    SystemService.forceDeleteSystem(system).then(function(response) {
      $uibModalInstance.close();
    }, $scope.addErrorAlert);
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.addErrorAlert = function(response) {
    $scope.alerts.push({
      type: 'danger',
      msg: _.get(response, 'data.message', 'Please check the server logs'),
    });
  };

  $scope.closeDialog = function() {
    $uibModalInstance.close();
  };
}
