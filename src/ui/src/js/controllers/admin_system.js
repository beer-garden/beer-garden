import _ from 'lodash';
import readLogs from '../../templates/read_logs.html';
import adminQueue from '../../templates/admin_queue.html';
import adminRequestDelete from '../../templates/admin_request_delete.html';
import forceDelete from '../../templates/system_force_delete.html';
import {responseState} from '../services/utility_service.js';

import gardenMetrics from '../../templates/admin_garden_metrics.html';

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
  'RequestService',
];

/**
 * adminSystemController - System management controller.
 * @param  {Object} $scope          Angular's $scope object.
 * @param  {Object} $rootScope      Angular's $rootScope object.
 * @param  {Object} $uibModal
 * @param  {Object} SystemService   Beer-Garden's system service object.
 * @param  {Object} InstanceService Beer-Garden's instance service object.
 * @param  {Object} UtilityService  Beer-Garden's utility service object.
 * @param  {Object} AdminService    Beer-Garden's admin service object.
 * @param  {Object} QueueService    Beer-Garden's event service object.
 * @param  {Object} RunnerService   Beer-Garden's runner service object.
 * @param  {Object} EventService    Beer-Garden's event service object.
 * @param  {Object} RequestService    Beer-Garden's request service object.
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
    RequestService,
) {
  $scope.response = undefined;
  $scope.runnerResponse = undefined;
  $scope.groupedSystems = [];
  $scope.alerts = [];
  $scope.runners = [];
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
        template: forceDelete,
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
        $scope.addErrorAlert,
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
    runner.waiting = true;
    RunnerService.startRunner(runner).catch($scope.addErrorAlert);
  };

  $scope.stopRunner = function(runner) {
    runner.waiting = true;
    RunnerService.stopRunner(runner).catch($scope.addErrorAlert);
  };

  $scope.deleteRunner = (runner) => {
    runner.waiting = true;
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
    return instanceFromRunner(runner) === undefined;
  };

  $scope.runnerInstanceName = function(runner) {
    return runner.instance ? runner.instance.name : 'UNKNOWN';
  };

  $scope.instanceIcon = function(instance) {
    if ('runner_id' in instance.metadata) {
      if (instance.metadata['runner_id'] != null && instance.metadata['runner_id'] != ""){
        for (const runner of $scope.runners) {
          if (runner.id == instance.metadata['runner_id'] && !runner.dead){
            if (instance.status == "UNRESPONSIVE"){
              return $rootScope.getIcon('fa-triangle-exclamation');
            }
            if (instance.status == "AWAITING_SYSTEM"){
              return $rootScope.getIcon('fa-hourglass')
            }
            return $rootScope.getIcon('fa-folder-open');
          }
        }
        return $rootScope.getIcon('fa-skull');
      }
    }
    return $rootScope.getIcon('fa-rss');
  }

  $scope.instanceIconTitle = function(instance) {
    if ('runner_id' in instance.metadata) {
      if (instance.metadata['runner_id'] != null && instance.metadata['runner_id'] != ""){
        for (const runner of $scope.runners) {
          if (runner.id == instance.metadata['runner_id']){
            if (!runner.dead) {
              return "../" + runner.path;
            }
            return "Subprocess dead: ../" + runner.path;
          }
        }
        return "Unable to find Local Runner";
      }
    }
    return 'Externally Managed'
  }

  $scope.addErrorAlert = function(response) {
    $scope.alerts.push({
      type: 'danger',
      msg:
        'Something went wrong on the backend: ' +
        _.get(response, 'data.message', 'Please check the server logs'),
    });
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  function groupSystems() {
    if ($rootScope.systems) {
      $scope.response = $rootScope.gardensResponse;

      const grouped = _.groupBy($rootScope.systems.filter($rootScope.isSystemRoutable), (value) => {
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

    // Need to grab a clean instance of runners each time
    RunnerService.getRunners().then((response) => {
      $scope.runnerResponse = response;
      $scope.runners = response.data;
  
      // This is kind of messy, but oh well
      if (responseState($scope.response) === 'empty') {
        $scope.response = response;
      }
  
      if ($scope.runners) {

        const unassociatedRunners = [];
  
        for (const runner of $scope.runners) {
  
          if ((runner.instance_id === undefined || runner.instance_id == null || runner.instance_id.length == 0) && $scope.isRunnerUnassociated(runner)) {
            unassociatedRunners.push(runner);
          }
        }
  
        const grouped = _.groupBy(unassociatedRunners, (value) => {
          return value.path;
        });
        $scope.groupedRunners = _.sortBy(grouped, (runnerList) => {
          return runnerList[0].path;
        });
      } else {
        $scope.groupedRunners = [];
      }
    });

    
  }

  $scope.hasUnassociatedRunners = function(runners) {
    for (const runner of runners) {
      if ($scope.isRunnerUnassociated(runner)) {
        return true;
      }
    }
    return false;
  };

  $scope.showLogs = function(system, instance) {
    
    $uibModal.open({
      template: readLogs,
      resolve: {
        system: system,
        instance: instance,
      },
      controller: 'AdminSystemLogsController',
      windowClass: 'app-modal-window',
    });
    
  };

  $scope.manageQueue = function(system, instance) {
    $uibModal.open({
      template: adminQueue,
      resolve: {
        system: system,
        instance: instance,
      },
      controller: 'AdminQueueController',
      windowClass: 'app-modal-window',
    });
  };

  $scope.cancelDeleteRequests = function (system, instance) {
    $uibModal.open({
      template: adminRequestDelete,
      resolve: {
        system: system,
        instance: instance,
      },
      controller: 'AdminRequestDeleteController',
      windowClass: 'app-modal-window',
    });
  };

  function eventCallback(event) {
    if ($rootScope.garden !== undefined && event.garden == $rootScope.garden.name) {
      if (event.name.startsWith('RUNNER') || event.name.startsWith('INSTANCE')) {
        groupRunners();
      }
    }
  }

  EventService.addCallback('admin_system', (event) => {
    $scope.$apply(() => {
      eventCallback(event);
    });
  });
  $scope.$on('$destroy', function() {
    EventService.removeCallback('admin_system');
  });

  function instanceFromRunner(runner) {
    if ($rootScope.systems !== undefined){
      for (const system of $rootScope.systems) {
        for (const instance of system.instances) {
          if (instance.metadata.runner_id == runner.id) {
            return instance;
          }
        }
      }
    }

    return undefined;
  }

  groupSystems();
  groupRunners();

  // Systems to load async, have to monitor the systems for changes
  $rootScope.$watchCollection('systems', function systemUpdate(){
    groupRunners();
    groupSystems();
  });
  
}
