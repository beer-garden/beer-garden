import angular from 'angular';
import _ from 'lodash';

adminSystemController.$inject = [
  '$scope',
  '$rootScope',
  '$interval',
  '$http',
  'localStorageService',
  'SystemService',
  'InstanceService',
  'UtilityService',
  'AdminService',
  'EventService',
];

/**
 * adminSystemController - System management controller.
 * @param  {$scope} $scope          Angular's $scope object.
 * @param  {$rootScope} $rootScope  Angular's $rootScope object.
 * @param  {$interval} $interval    Angular's $interval object.
 * @param  {$http} $http            Angular's $http object.
 * @param  {localStorageService} localStorageService Storage service
 * @param  {Object} SystemService   Beer-Garden's system service object.
 * @param  {Object} InstanceService Beer-Garden's instance service object.
 * @param  {Object} UtilityService  Beer-Garden's utility service object.
 * @param  {Object} AdminService    Beer-Garden's admin service object.
 * @param  {Object} EventService    Beer-Garden's event service object.
 */
export default function adminSystemController(
    $scope,
    $rootScope,
    $interval,
    $http,
    localStorageService,
    SystemService,
    InstanceService,
    UtilityService,
    AdminService,
    EventService) {
  $scope.setWindowTitle('systems');

  $scope.util = UtilityService;

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
    return system.instances.some(function(instance) {
      return instance.status == 'RUNNING';
    });
  };

  $scope.startInstance = function(instance) {
    InstanceService.startInstance(instance).then(
      () => {
        instance.status = 'STARTING';
      },
      $scope.addErrorAlert
    );
  };

  $scope.stopInstance = function(instance) {
    InstanceService.stopInstance(instance).then(
      () => {
        instance.status = 'STOPPING';
      },
      $scope.addErrorAlert
    );
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

  $scope.successCallback = function(response) {
    $scope.response = response;
    $rootScope.systems = response.data;

    $scope.data = _.groupBy(response.data, (value) => {
      return value.display_name || value.name;
    });
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = [];
  };

  /**
   * updateInstanceStatus - Change the status of an instance
   * @param {string} id  The instance ID
   * @param {string} newStatus  The new status
   */
  function updateInstanceStatus(id, newStatus) {
    if (newStatus === undefined) return;

    for (let systemName in $scope.data) {
      if ({}.hasOwnProperty.call($scope.data, systemName)) {
        for (let system of $scope.data[systemName]) {
          for (let instance of system.instances) {
            if (instance.id === id) {
              instance.status = newStatus;
            }
          }
        }
      }
    }
  }

  /**
   * removeSystem - Remove a system from the list of systems
   * @param {string} id  The system ID
   */
  function removeSystem(id) {
    for (let systemName in $scope.data) {
      if ({}.hasOwnProperty.call($scope.data, systemName)) {
        for (let system of $scope.data[systemName]) {
          if (system.id === id) {
            _.pull($scope.data[systemName], system);

            if ($scope.data[systemName].length === 0) {
              delete $scope.data[systemName];
            }
          }
        }
      }
    }
  }

  let loadSystems = function() {
    SystemService.getSystems(
      {includeFields: 'id,name,display_name,version,instances'}
    ).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  };

  // Periodically poll for changes (in case of websocket failure)
  let systemsUpdate = $interval(function() {
    loadSystems();
  }, 5000);

  // Need to clean up the interval and callback when done
  $scope.$on('$destroy', function() {
    if (angular.isDefined(systemsUpdate)) {
      $interval.cancel(systemsUpdate);
      systemsUpdate = undefined;
    }

    EventService.clearCallback();
  });

  let loadAll = function() {
    $scope.response = undefined;
    $scope.data = [];
    $scope.alerts = [];

    loadSystems();
  };

  EventService.setCallback((message) => {
    let event = JSON.parse(message.data);

    switch (event.name) {
      case 'INSTANCE_INITIALIZED':
        updateInstanceStatus(event.payload.id, 'RUNNING');
        break;
      case 'INSTANCE_STOPPED':
        updateInstanceStatus(event.payload.id, 'STOPPED');
        break;
      case 'SYSTEM_REMOVED':
        removeSystem(event.payload.id);
        break;
    }
  });

  $scope.$on('userChange', function() {
    loadAll();
  });

  loadAll();
};
