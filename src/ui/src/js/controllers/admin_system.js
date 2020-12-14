import _ from 'lodash';
import readLogs from '../../templates/read_logs.html';
import adminQueue from '../../templates/admin_queue.html';
import forceDelete from '../../templates/system_force_delete.html';

adminSystemController.$inject = [
  '$scope',
  '$rootScope',
  '$uibModal',
  'SystemService',
  'InstanceService',
  'UtilityService',
  'AdminService',
  'QueueService',
  'RunnerService',
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
 * @param  {Object} QueueService    Beer-Garden's event service object.
 * @param  {Object} RunnerService   Beer-Garden's runner service object.
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
    QueueService,
    RunnerService,
    EventService,
    ) {
  $scope.response = undefined;
  $scope.runnerResponse = undefined;
  $scope.groupedSystems = [];
  $scope.alerts = [];
  $scope.runners = [];
  $scope.showRunnersTile = false;
  $scope.groupedRunners = [];

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

    $scope.deletedSystem = system;
    SystemService.deleteSystem(system).then(_.noop, (response) => {
        $uibModal.open({
         template:forceDelete,
        resolve: {
           system: $scope.deletedSystem,
           response: response,
         },
         controller: 'AdminSystemForceDeleteController',
         windowClass: 'app-modal-window',
      });
    });

  };

  $scope.clearAllQueues = function() {
    QueueService.clearQueues().then(
      $scope.addSuccessAlert,
      $scope.addErrorAlert
    );
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

  $scope.startRunner = function(runner) {
    RunnerService.startRunner(runner).catch($scope.addErrorAlert);
  };

  $scope.stopRunner = function(runner) {
    RunnerService.stopRunner(runner).catch($scope.addErrorAlert);
  };

  $scope.deleteRunner = (runner) => {
    RunnerService.removeRunner(runner).catch($scope.addErrorAlert);
  };

  $scope.startRunners = function(runnerList) {
    _.forEach(runnerList, $scope.startRunner);
  };

  $scope.stopRunners = function(runnerList) {
    _.forEach(runnerList, $scope.stopRunner);
  };

  $scope.reloadRunners = function(runnerList) {
    RunnerService.reloadRunners(runnerList[0].path).catch($scope.addErrorAlert);
  };

  $scope.deleteRunners = function(runnerList) {
    _.forEach(runnerList, $scope.deleteRunner);
  };

  $scope.isRunnerUnassociated = function(runner) {
    return !runner.instance_id || runner.instance_id == '';
  };

  $scope.runnerInstanceName = function(runner) {
    return runner.instance ? runner.instance.name : "UNKNOWN";
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

  function groupRunners() {
    if ($scope.runners) {
      $scope.showRunnersTile = false;

      for (let runner of $scope.runners) {
        runner.instance = instanceFromRunner(runner);

        if ($scope.isRunnerUnassociated(runner)){
          $scope.showRunnersTile = true;
        }
      }

      let grouped = _.groupBy($scope.runners, (value) => {
        return value.path;
      });
      $scope.groupedRunners = _.sortBy(grouped, (runnerList) => {
        return runnerList[0].path;
      });
    } else {
      $scope.groupedRunners = [];
    }
  }

  $scope.hasUnassociatedRunners = function(runners) {
    for (let runner of runners) {
      if ($scope.isRunnerUnassociated(runner)) {
        return true;
      }
    }
    return false;
  };

  $rootScope.$watchCollection("systems", groupSystems);

  $scope.showLogs = function (system, instance) {
       $uibModal.open({
         template:readLogs,
         resolve: {
           system: system,
           instance: instance,
         },
         controller: 'AdminSystemLogsController',
         windowClass: 'app-modal-window',
      });
    };

  $scope.manageQueue = function (system, instance) {
       $uibModal.open({
         template:adminQueue,
         resolve: {
           system: system,
           instance: instance,
         },
         controller: 'AdminQueueController',
         windowClass: 'app-modal-window',
      });
    };

  function eventCallback(event) {
    if (event.name.startsWith('RUNNER')) {
      _.remove($scope.runners, (value) => {
        return value.id == event.payload.id;
      });

      if (event.name != 'RUNNER_REMOVED') {
        $scope.runners.push(event.payload);
      }
      groupRunners();

    }
    else if (event.name.startsWith('INSTANCE')) {
      groupRunners();
    }
  }

  EventService.addCallback('admin_system', (event) => {
    $scope.$apply(() => {eventCallback(event);})
  });
  $scope.$on('$destroy', function() {
    EventService.removeCallback('admin_system');
  });

  function instanceFromRunner(runner) {
    for (let system of $rootScope.systems) {
      for (let instance of system.instances) {
        if (instance.metadata.runner_id == runner.id) {
          return instance;
        }
      }
    }

    return undefined;
  }

  groupSystems();

  RunnerService.getRunners().then((response) => {
    $scope.runnerResponse = response;
    $scope.runners = response.data;

    groupRunners();
  });

};
