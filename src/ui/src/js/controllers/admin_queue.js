import angular from 'angular';

adminQueueController.$inject = [
  '$scope',
  '$uibModalInstance',
  '$interval',
  'QueueService',
  'system',
  'instance',
];

/**
 * adminQueueController - Angular controller for queue index page.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $uibModalInstance Modal instance.
 * @param  {Object} $interval         Angular's $interval object.
 * @param  {Object} QueueService      Beer-Garden's queue service object.
 * @param  {Object} system
 * @param  {Object} instance
 */
export default function adminQueueController(
    $scope,
    $uibModalInstance,
    $interval,
    QueueService,
    system,
    instance,
) {
  $scope.alerts = [];
  $scope.system = system;
  $scope.instance = instance;
  $scope.queues = [];

  $scope.clearQueue = function(queueName) {
    QueueService.clearQueue(queueName).then(
        $scope.addSuccessAlert,
        $scope.failureCallback,
    );
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.addSuccessAlert = function(response) {
    $scope.alerts.push({
      type: 'success',
      msg: 'Success! Please allow 10 seconds for the message counts to update.',
    });
  };

  $scope.addErrorAlert = function(response) {
    let msg = 'Uh oh! It looks like there was a problem clearing the queue.\n';
    if (response.data !== undefined && response.data !== null) {
      msg += response.data;
    }
    $scope.alerts.push({
      type: 'danger',
      msg: msg,
    });
  };

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.queues = response.data;
    return response.data;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
  };

  $scope.closeDialog = function() {
    if (angular.isDefined(poller)) {
      $interval.cancel(poller);
      poller = undefined;
    }

    $uibModalInstance.close();
  };

  let poller = $interval(function() {
    loadQueues();
  }, 10000);

  $scope.$on('$destroy', function() {
    if (angular.isDefined(poller)) {
      $inteval.cancel(poller);
      poller = undefined;
    }
  });

  function loadQueues() {
    $scope.response = undefined;

    $scope.queues = QueueService.getInstanceQueues($scope.instance.id).then(
        $scope.successCallback,
        $scope.addErrorAlert,
    );
  }

  loadQueues();
}
