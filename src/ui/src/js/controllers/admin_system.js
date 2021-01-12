import _ from 'lodash';
import readLogs from '../../templates/read_logs.html';
import adminQueue from '../../templates/admin_queue.html';
import forceDelete from '../../templates/system_force_delete.html';
import {responseState} from '../services/utility_service.js';

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
  $scope.groupedSystemsNamespaces = [];
  $scope.alerts = [];
  $scope.runners = [];
  $scope.showRunnersTile = false;
  $scope.groupedRunners = [];
  $scope.systemHidden = [];
  $scope.versionHidden = [];
  $scope.namespaceHidden = [];
  $scope.system_name_query = null;

  $scope.totalInstancesInSystem = function (groupedSystems){
    let count = 0;
    let groupedNamespaces = [];
    for (let i = 0; i < groupedSystems.length; i++){
        groupedNamespaces = groupedSystems[i];
        for (let j = 0; j < groupedNamespaces.length; j++) {
            count += groupedNamespaces[j].instances.length;
        }
    }
    return count;
  };

  $scope.totalVersionsInSystem = function (groupedSystems){
      let count = 0;
      let groupedNamespaces = [];
      for (let i = 0; i < groupedSystems.length; i++){
        count += groupedSystems[i].length;
      }
      return count;
    };

  $scope.totalRunningIdsInRunner = function (runners) {
    let count = 0;
    for (let i = 0; i < runners.length; i++) {
        if (runners[i].instance != undefined) {
            count++;
        }
    }
    return count
  };

  $scope.totalRunningInSystem = function (groupedSystems){
      let count = 0;
      let system = {};
      let systems = [];
      let instance = {};
      let groupedNamespaces = [];
      for (let i = 0; i < groupedSystems.length; i++){
        systems = groupedSystems[i];
          for (let k = 0; k < systems.length; k++) {
            system = systems[k];
            for (let m = 0; m < system.instances.length; m++) {
              instance = system.instances[m];
              if (instance.status == "RUNNING") {
                count++;
              }
            }
          }
      }
      return count;
    };

  $scope.stopSystems = function(groupedSystems=[], systems=[], namespace="") {
    let system = {};
    if (groupedSystems[0] == undefined) {
        groupedSystems[0] = systems;
    }
    for (let i = 0; i < groupedSystems.length; i++) {
        systems = groupedSystems[i];
        for (let j = 0; j < systems.length; j++) {
            system = systems[j];
            if (namespace == "" || namespace == system.namespace) {
                $scope.stopSystem(system);
            }
        }
    }
    return;
  };

  $scope.deleteMessage = function(groupedSystems=[], systems=[], namespace="") {
    let msg = "Are you sure you want to delete systems listed below?\nActive systems:{active}\nInactive Systems:{inactive}";
    if (groupedSystems[0] == undefined) {
        groupedSystems[0] = systems;
    }
    let system = {};
    let msg_inactive = "";
    let msg_active = "";
    for (let i = 0; i < groupedSystems.length; i++) {
        systems = groupedSystems[i];
        for (let j = 0; j < systems.length; j++) {
            system = systems[j];
            if (namespace == "" || namespace == system.namespace) {
                if ($scope.hasRunningInstances(system)) {
                    msg_active = msg_active.concat("\n\u2022 {namespace}: {system_name}-{version} ");
                    msg_active = msg_active.replace('{system_name}', system.name).replace('{namespace}', system.namespace).replace('{version}', system.version);
                }
                else {
                    msg_inactive = msg_inactive.concat("\n\u2022 {namespace}: {system_name}-{version} ");
                    msg_inactive = msg_inactive.replace('{system_name}', system.name).replace('{namespace}', system.namespace).replace('{version}', system.version);
                }
            }
        }
    }
    return msg.replace('{active}', msg_active).replace('{inactive}', msg_inactive)
  };

  $scope.deleteSystems = function(groupedSystems=[], systems=[], namespace="") {
       if (groupedSystems[0] == undefined) {
            groupedSystems[0] = systems;
       }
       let system = {};
      for (let i = 0; i < groupedSystems.length; i++) {
          systems = groupedSystems[i];
          for (let j = 0; j < systems.length; j++) {
              system = systems[j];
              if (namespace == "" || namespace == system.namespace) {
                  $scope.deleteSystem(system);
              }
          }
      }
    };

  $scope.expandAll = function (){
    let key = undefined;
    for (key in $scope.systemHidden) {
        $scope.systemHidden[key] = false;
    }
    for (key in $scope.namespaceHidden) {
            $scope.namespaceHidden[key] = false;
    }
    for (key in $scope.versionHidden) {
            $scope.versionHidden[key] = false;
    }
  };

  $scope.collapseAll = function (){
      let key = undefined;
      for (key in $scope.systemHidden) {
          $scope.systemHidden[key] = true;
      }
      for (key in $scope.namespaceHidden) {
              $scope.namespaceHidden[key] = true;
      }
      for (key in $scope.versionHidden) {
              $scope.versionHidden[key] = true;
      }
  };

  function expandNotRunning(groupedSystems) {
    let system = {};
    let systems = [];
    let instance = {};
    for (let k = 0; k < groupedSystems.length; k++) {
        systems = groupedSystems[k];
        $scope.systemHidden[systems[0].name] = true;
        for (let i = 0; i < systems.length; i++) {
            system = systems[i];
            if ($scope.namespaceHidden[system.name.concat(system.namespace)] == undefined) {
                $scope.namespaceHidden[system.name.concat(system.namespace)] = true;
            }
            $scope.versionHidden[system.name.concat(system.namespace).concat(system.version)] = true;
            for (let j = 0; j < system.instances.length; j++) {
                instance = system.instances[j];
                if (instance.status != "RUNNING"){
                    $scope.systemHidden[systems[0].name] = false;
                    $scope.namespaceHidden[system.name.concat(system.namespace)] = false;
                    $scope.versionHidden[system.name.concat(system.namespace).concat(system.version)] = false;
                }
            }
        }
    }
  };

   $scope.reloadSystems = function(groupedSystems=[], systems=[], namespace="") {
         if (groupedSystems[0] == undefined) {
              groupedSystems[0] = systems;
         }
         let system = {};
        for (let i = 0; i < groupedSystems.length; i++) {
            systems = groupedSystems[i];
            for (let j = 0; j < systems.length; j++) {
               system = systems[j];
               if (namespace == "" || namespace == system.namespace) {
                   $scope.reloadSystem(system)
               }
            }
       }
       return;
     };

   $scope.startSystems = function(groupedSystems=[], systems=[], namespace="") {
        if (groupedSystems[0] == undefined) {
             groupedSystems[0] = systems;
        }
        let system = {};
       for (let i = 0; i < groupedSystems.length; i++) {
           systems = groupedSystems[i];
           for (let j = 0; j < systems.length; j++) {
               system = systems[j];
               if (namespace == "" || namespace == system.namespace) {
                   $scope.startSystem(system);
               }
           }
       }
       return;
     };

  $scope.totalNamespacesInSystem = function (systems){
        let count = 0;
        let namespace_list = [];
        for (let system in systems){
            if (systems[system].namespace) {
                if (!namespace_list.includes(systems[system].namespace)) {
                  count++;
                  namespace_list.push(systems[system].namespace)
                }
            }
        }
        return count;
      };

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
      groupNamespaces()
    } else {
      $scope.groupedSystems = [];
    }
  }

  function groupNamespaces() {
        let group = {};
        let tmp_system = {};
        let systems = [];
        let system = {};
        let count = 0;
        for (let i = 0; i < $scope.groupedSystems.length; i++) {
            systems = $scope.groupedSystems[i];
            group = {};
            for (let j = 0; j < systems.length; j++) {
                system = systems[j];
                if (group[system.namespace] == undefined) {
                    group[system.namespace] = [];
                }
                group[system.namespace][group[system.namespace].length] = system;
            }
            let count = 0;
            for (let key in group) {
                if ($scope.groupedSystemsNamespaces[i] == undefined) {
                    $scope.groupedSystemsNamespaces[i] = [];
                }
                $scope.groupedSystemsNamespaces[i][count] = group[key];
                count++;
            }
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

  expandNotRunning($scope.groupedSystems);

  RunnerService.getRunners().then((response) => {
    $scope.runnerResponse = response;
    $scope.runners = response.data;

    // This is kind of messy, but oh well
    if (responseState($scope.response) === 'empty') {
      $scope.response = response;
    }

    groupRunners();
  });

};
