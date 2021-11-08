adminSystemLogsController.$inject = [
  "$scope",
  "$uibModalInstance",
  "InstanceService",
  "system",
  "instance",
];

/**
 * adminSystemController - System management controller.
 * @param  {Object} $scope          Angular's $scope object.
 * @param  {Object} $rootScope      Angular's $rootScope object.
 * @param  {Object} SystemService   Beer-Garden's system service object.
 * @param  {Object} InstanceService Beer-Garden's instance service object.
 */
export default function adminSystemLogsController(
  $scope,
  $uibModalInstance,
  InstanceService,
  system,
  instance
) {
  $scope.logs = undefined;
  $scope.start_line = 0;
  $scope.end_line = 20;
  $scope.tail_line = 20;
  $scope.wait_timeout = 30;
  $scope.displayLogs = undefined;
  $scope.system = system;
  $scope.instance = instance;
  $scope.loadingLogs = false;
  $scope.alerts = [
    {
      type: "info",
      msg:
        "Plugin must be listening to the Admin Queue " +
        "and logging to File for logs to be returned. " +
        "This will only return information from the log file being actively written to.",
    },
  ];

  $scope.downloadHref = undefined;
  $scope.filename =
    $scope.system.name +
    "[" +
    $scope.system.version +
    "]-" +
    $scope.instance.name +
    ".log";

  $scope.successLogs = function (response) {
    $scope.loadingLogs = false;
    $scope.logs = response.data;
    $scope.displayLogs = "";
    $scope.requestId = response.headers("request_id");

    for (var i = 0; i < $scope.logs.length; i++) {
      $scope.displayLogs = $scope.displayLogs.concat($scope.logs[i]);
    }

    $scope.downloadHref = "api/v1/requests/output/" + $scope.requestId;
  };

  $scope.getLogsLines = function () {
    $scope.loadingLogs = true;
    $scope.displayLogs = undefined;

    InstanceService.getInstanceLogs(
      instance.id,
      $scope.wait_timeout,
      $scope.start_line,
      $scope.end_line
    ).then($scope.successLogs, $scope.addErrorAlert);
  };

  $scope.getLogsTail = function () {
    $scope.loadingLogs = true;
    $scope.displayLogs = undefined;

    InstanceService.getInstanceLogs(
      instance.id,
      $scope.wait_timeout,
      $scope.tail_line * -1,
      null
    ).then($scope.successLogs, $scope.addErrorAlert);
  };

  $scope.getLogs = function () {
    $scope.loadingLogs = true;
    $scope.displayLogs = undefined;

    InstanceService.getInstanceLogs(
      instance.id,
      $scope.wait_timeout,
      null,
      null
    ).then($scope.successLogs, $scope.addErrorAlert);
  };

  $scope.closeDialog = function () {
    $uibModalInstance.close();
  };

  $scope.closeAlert = function (index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.addErrorAlert = function (response) {
    $scope.loadingLogs = false;
    $scope.alerts.push({
      type: "danger",
      msg:
        "Something went wrong on the backend: " +
        _.get(response, "data.message", "Please check the server logs"),
    });
  };
}
