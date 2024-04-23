adminSystemLogsController.$inject = [
  '$scope',
  '$uibModalInstance',
  '$timeout',
  'InstanceService',
  'system',
  'instance',
];

/**
 * adminSystemController - System management controller.
 * @param  {Object} $scope          Angular's $scope object.
 * @param  {Object} $uibModalInstance
 * @param  {Object} $timeout
 * @param  {Object} InstanceService Beer-Garden's instance service object.
 * @param  {Object} system
 * @param  {Object} instance
 */
export default function adminSystemLogsController(
    $scope,
    $uibModalInstance,
    $timeout,
    InstanceService,
    system,
    instance,
) {
  $scope.logs = undefined;
  $scope.start_line = 0;
  $scope.end_line = 20;
  $scope.tail_start = 0;
  $scope.tail_line = 20;
  $scope.wait_timeout = 30;
  $scope.displayLogs = undefined;
  $scope.system = system;
  $scope.instance = instance;
  $scope.loadingLogs = false;
  $scope.stopTailing = false;
  $scope.alerts = [
    {
      type: 'info',
      msg:
        'Plugin must be listening to the Admin Queue ' +
        'and logging to File for logs to be returned. ' +
        'This will only return information from the log file being actively written to.',
    },
  ];

  $scope.downloadHref = undefined;
  $scope.filename =
    $scope.system.name +
    '[' +
    $scope.system.version +
    ']-' +
    $scope.instance.name +
    '.log';

  $scope.successLogs = function(response) {
    $scope.loadingLogs = false;
    $scope.logs = response.data;
    $scope.displayLogs = '';
    $scope.requestId = response.headers('request_id');

    for (let i = 0; i < $scope.logs.length; i++) {
      $scope.displayLogs = $scope.displayLogs.concat($scope.logs[i]);
    }

    $scope.downloadHref = 'api/v1/requests/output/' + $scope.requestId;
  };


  $scope.getLogsLines = function() {
    $scope.loadingLogs = true;
    $scope.displayLogs = undefined;


    InstanceService.getInstanceLogs(
        instance.id,
        $scope.wait_timeout,
        $scope.start_line,
        $scope.end_line,
    ).then($scope.successLogs, $scope.addErrorAlert);
  };

  $scope.successTailLogs = function(response) {
    $scope.loadingLogs = false;
    let appendLogs = true;

    if ($scope.displayLogs === undefined){
      $scope.displayLogs = '';
      $scope.logs = [];
      appendLogs = false;
    } 

    for (let i = 0; i < response.data.length; i++) {
      $scope.displayLogs = $scope.displayLogs.concat(response.data[i]);
    }

    $scope.requestId = response.headers('request_id');
    $scope.downloadHref = 'api/v1/requests/output/' + $scope.requestId;

    if (response.data.length > 0){
      $scope.tail_start = $scope.tail_start + response.data.match(/\n/g).length + 1;
    }

    // Sleep so you don't spam the server
    if (response.data.length == 0 || response.data.match(/\n/g).length < $scope.tail_line){
      $timeout(() => {$scope.getLogsTailLoop();}, 10000); // Sleep Ten seconds
    } else {
      $timeout(() => {$scope.getLogsTailLoop();}, 1000); // Sleep One Second
    }
    ;
  };

  $scope.getLogsTailLoop = function() {
    if ($scope.stopTailing) {
      return;
    }
    InstanceService.getInstanceLogs(
        instance.id,
        $scope.wait_timeout,
        $scope.tail_start,
        $scope.tail_line + $scope.tail_start,
    ).then($scope.successTailLogs, $scope.addErrorAlert);
  };

  $scope.stopLogsTail = function() {
    $scope.stopTailing = true;
  }

  $scope.getLogsTail = function() {
    $scope.loadingLogs = true;
    $scope.displayLogs = undefined;
    $scope.tail_start = 0;
    $scope.stopTailing = false;

    InstanceService.getInstanceLogs(
        instance.id,
        $scope.wait_timeout,
        $scope.tail_start,
        $scope.tail_line + $scope.tail_start,
    ).then($scope.successTailLogs, $scope.addErrorAlert);
  };

  $scope.getLogs = function() {
    $scope.loadingLogs = true;
    $scope.displayLogs = undefined;

    InstanceService.getInstanceLogs(
        instance.id,
        $scope.wait_timeout,
        null,
        null,
    ).then($scope.successLogs, $scope.addErrorAlert);
  };

  $scope.closeDialog = function() {
    $scope.stopTailing = true;
    $uibModalInstance.close();
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.addErrorAlert = function(response) {
    $scope.loadingLogs = false;
    $scope.alerts.push({
      type: 'danger',
      msg:
        'Something went wrong on the backend: ' +
        _.get(response, 'data.message', 'Please check the server logs'),
    });
  };
}
