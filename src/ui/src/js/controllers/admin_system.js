import _ from 'lodash';

adminSystemController.$inject = [
  '$scope',
  '$rootScope',
  '$uibModal',
  'SystemService',
  'InstanceService',
  'UtilityService',
  'AdminService',
  'EventService',
];

/**
 * adminSystemController - System management controller.
 * @param  {Object} $scope          Angular's $scope object.
 * @param  {Object} $rootScope      Angular's $rootScope object.
 * @param  {Object} SystemService   Beer-Garden's system service object.
 * @param  {Object} InstanceService Beer-Garden's instance service object.
 * @param  {Object} UtilityService  Beer-Garden's utility service object.
 * @param  {Object} AdminService    Beer-Garden's admin service object.
 * @param  {Object} EventService    Beer-Garden's event service object.
 */
export default function adminSystemController(
    $scope,
    $rootScope,
    $uibModal,
    SystemService,
    InstanceService,
    UtilityService,
    AdminService,
    EventService,
    ) {
  $scope.response = undefined;
  $scope.groupedSystems = [];
  $scope.alerts = [];

  $scope.setWindowTitle('systems');

  $scope.getIcon = UtilityService.getIcon;

  $scope.rescan = function() {
    AdminService.rescan().then(_.noop, $scope.addErrorAlert);
  };

  $scope.startSystem = function(system) {
    _.forEach(system.instances, $scope.startInstance);
  };

  $scope.stopSystem = function(system) {
    _.forEach(system.instances, $scope.stopInstance);
  };

  $scope.reloadSystem = function(system) {
    SystemService.reloadSystem(system).then(_.noop, $scope.addErrorAlert);
  };

  $scope.deleteSystem = function(system) {
    SystemService.deleteSystem(system).then(_.noop, $scope.addErrorAlert);
  };

  $scope.hasRunningInstances = function(system) {
    return system.instances.some((instance) => {
      return instance.status == 'RUNNING';
    });
  };

  $scope.startInstance = function(instance) {
    InstanceService.startInstance(instance).catch($scope.addErrorAlert);
  };

  $scope.stopInstance = function(instance) {
    InstanceService.stopInstance(instance).catch($scope.addErrorAlert);
  };

  $scope.addErrorAlert = function(response) {
    $scope.alerts.push({
      type: 'danger',
      msg: 'Something went wrong on the backend: ' +
        _.get(response, 'data.message', 'Please check the server logs'),
    });
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  function groupSystems() {
    if ($rootScope.systems) {
      $scope.response = $rootScope.sysResponse;

      let grouped = _.groupBy($rootScope.systems, (value) => {
        return value.display_name || value.name;
      });
      $scope.groupedSystems = _.sortBy(grouped, (sysList) => {
        return sysList[0].display_name || sysList[0].name;
      });
    } else {
      $scope.groupedSystems = [];
    }
  }

  EventService.addCallback('admin_system', (event) => {
    if (event.name.startsWith('SYSTEM') || event.name.startsWith('INSTANCE')) {
      $scope.$apply(groupSystems);
    }
  });
  $scope.$on('$destroy', function() {
    EventService.removeCallback('admin_system');
  });

  $scope.showLogs = function (system, instance) {
       $uibModal.open({
         template:
           '<div class="modal-header">' +
           '  <h3 class="modal-title" id="modal-title">Log File: {{system.name}}[{{system.version}}]-{{instance.name}}</h3>' +
           '</div>' +
           '<div class="modal-body" id="modal-body">' +
           '<div uib-alert' +
           '     ng-repeat="alert in alerts"' +
           '     ng-class="\'alert-\' + alert.type"' +
           '     close="closeAlert($index)">' +
           '  {{alert.msg}}' +
           '</div>' +
           '<div>' +
           '    <form ng-submit="getLogsTail()">' +
           '      <input type="submit" value="Get Tail Logs">' +
           '      <label for="start_line">Tail Lines</label>' +
           '      <input type="number" id="tail_line" min="0" name="start_line" ng-model="tail_line">' +
           '    </form>' +
           '  </div>' +
           '<div>' +
           '    <form ng-submit="getLogsLines()">' +
           '      <input type="submit" value="Get Line Logs">' +
           '      <label for="start_line">Start Line</label>' +
           '      <input type="number" id="start_line" min="0" name="start_line" ng-model="start_line">' +
           '      <label for="end_line">End Line</label>' +
           '      <input type="number" id="end_line" min="0" name="end_line" ng-model="end_line">' +
           '    </form>' +
           '  </div>' +
           '<div>' +
           '    <form ng-submit="getLogs()">' +
           '      <input type="submit" value="Get Full Logs">' +
           '    </form>' +
           '</div>' +
           '<div id="loading"' +
           '       class="col-md-12 text-center"' +
           '       ng-if="loadingLogs">' +
           '    <h1 ng-show="loadingLogs">' +
           '      <div>Loading...</div>' +
           '      <div><i class="fa fa-spinner fa-pulse fa-2x"></i></div>' +
           '    </h1>' +
           '  </div>' +
           '  <div class="container-fluid animate-if"' +
           '       ng-if="logs !== undefined">' +
           '    <br>' +
           '    <a class="fa fa-download pull-right" ' +
           '      ng-href="{{downloadHref}}" download="{{filename}}" ng-show="displayLogs !== undefined"></a>' +
           '    <pre id="rawOutput" ng-show="displayLogs !== undefined">{{displayLogs}}</pre>' +
           '  </div>' +
           '</div>' +

           '<div class="modal-footer">' +
           '    <button class="btn btn-primary" type="button" ng-click="closeDialog()">Close Logs</button>' +
           '</div>',
         resolve: {
           InstanceService: InstanceService,
           system: system,
           instance: instance,
         },
         controller: adminSystemLogsController,
         windowClass: 'app-modal-window',
      });
      function adminSystemLogsController ($scope, $uibModalInstance, InstanceService, system, instance){
          $scope.logs = undefined;
          $scope.start_line = 0;
          $scope.end_line = 20;
          $scope.tail_line=20;
          $scope.wait_timeout = 30
          $scope.displayLogs = undefined;
          $scope.system = system;
          $scope.instance = instance;
          $scope.loadingLogs = false
          $scope.alerts = [{
                              type: 'info',
                              msg: 'Plugin must be listening to the Admin Queue ' +
                                   'and logging to File for logs to be returned. '+
                                   'This will only return information from the log file being actively written to.',
                            }];



          $scope.downloadHref = undefined;
          $scope.filename = $scope.system.name+"["+$scope.system.version+"]-"+$scope.instance.name+".log";

          $scope.successLogs = function(response) {
            $scope.loadingLogs = false
            $scope.logs = response.data;
            $scope.displayLogs = "";

            for (var i = 0; i < $scope.logs.length; i++ ){
                $scope.displayLogs = $scope.displayLogs.concat($scope.logs[i]);
            };
            $scope.downloadHref = 'data:text/plain;charset=utf-8,' + encodeURIComponent($scope.displayLogs);
          }

          $scope.getLogsLines = function(){
            $scope.loadingLogs = true;
            $scope.displayLogs = undefined;
            InstanceService.showInstanceLogLines(instance.id, $scope.wait_timeout, $scope.start_line, $scope.end_line).then($scope.successLogs, $scope.addErrorAlert);
          };
          $scope.getLogsTail = function(){
            $scope.loadingLogs = true;
            $scope.displayLogs = undefined;
            InstanceService.showInstanceLogTail(instance.id, $scope.wait_timeout, $scope.tail_line).then($scope.successLogs, $scope.addErrorAlert);
          };
          $scope.getLogs = function(){
            $scope.loadingLogs = true;
            $scope.displayLogs = undefined;
            InstanceService.showInstanceLog(instance.id, $scope.wait_timeout).then($scope.successLogs, $scope.addErrorAlert);
          };

          $scope.closeDialog = function() {
            $uibModalInstance.close();
          }

          $scope.closeAlert = function(index) {
            $scope.alerts.splice(index, 1);
          };

          $scope.addErrorAlert = function(response) {
            $scope.loadingLogs = false
            $scope.alerts.push({
              type: 'danger',
              msg: 'Something went wrong on the backend: ' +
                _.get(response, 'data.message', 'Please check the server logs'),
            });
  };
      }
    };

  groupSystems();
};
