import angular from 'angular';
import _ from 'lodash';

adminSystemController.$inject = [
  '$scope',
  '$rootScope',
  '$interval',
  '$http',
  '$websocket',
  'localStorageService',
  'SystemService',
  'InstanceService',
  'UtilityService',
  'AdminService',
];

/**
 * adminSystemController - System management controller.
 * @param  {$scope} $scope          Angular's $scope object.
 * @param  {$rootScope} $rootScope  Angular's $rootScope object.
 * @param  {$interval} $interval    Angular's $interval object.
 * @param  {$http} $http            Angular's $http object.
 * @param  {$websocket} $websocket  Angular's $websocket object.
 * @param  {localStorageService} localStorageService Storage service
 * @param  {Object} SystemService   Beer-Garden's system service object.
 * @param  {Object} InstanceService Beer-Garden's instance service object.
 * @param  {Object} UtilityService  Beer-Garden's utility service object.
 * @param  {Object} AdminService    Beer-Garden's admin service object.
 */
export default function adminSystemController(
    $scope,
    $rootScope,
    $interval,
    $http,
    $websocket,
    localStorageService,
    SystemService,
    InstanceService,
    UtilityService,
    AdminService) {
  $scope.util = UtilityService;

  $scope.systems = {
    data: [],
    loaded: false,
    error: false,
    errorMessage: '',
    forceReload: false,
    status: null,
    errorMap: {
      'empty': {
        'solutions': [
          {
            problem: 'Backend Down',
            description: 'If the backend is down, there will be no systems to control',
            resolution: '<kbd>service bartender start</kbd>',
          },
          {
            problem: 'Plugin Problems',
            description: 'If Plugins attempted to start, but are failing to startup, then' +
                         'you\'ll have to contact the plugin maintainer. You can tell what\'s ' +
                         'wrong by their logs. Plugins are located at ' +
                         '<code>$APP_HOME/plugins</code>',
            resolution: '<kbd>less $APP_HOME/log/my-plugin.log</kbd>',
          },
          {
            problem: 'Database Names Do Not Match',
            description: 'It is possible that the backend is pointing to a Different Database ' +
                         'than the Frontend. Check to make sure that the <code>DB_NAME</code> ' +
                         'in both config files is the same',
            resolution: '<kbd>vim $APP_HOME/conf/bartender.json</kbd><br />' +
                        '<kbd>vim $APP_HOME/conf/brew-view.json</kbd>',
          },
          {
            problem: 'There Are No Systems',
            description: 'If no one has ever developed any plugins, then there will be no ' +
                          'systems here. You\'ll need to build your own plugins.',
            resolution: 'Develop a Plugin',
          },
        ],
      },
    },
  };

  $scope.rescan = function() {
    AdminService.rescan();
  };

  $scope.startSystem = function(system) {
    _.forEach(system.instances, $scope.startInstance);
  };

  $scope.stopSystem = function(system) {
    _.forEach(system.instances, $scope.stopInstance);
  };

  $scope.reloadSystem = function(system) {
    SystemService.reloadSystem(system);
  };

  $scope.deleteSystem = function(system) {
    SystemService.deleteSystem(system);
  };

  $scope.hasRunningInstances = function(system) {
    return system.instances.some(function(instance) {
      return instance.status == 'RUNNING';
    });
  };

  $scope.startInstance = function(instance) {
    instance.status = 'STARTING';
    InstanceService.startInstance(instance);
  };

  $scope.stopInstance = function(instance) {
    instance.status = 'STOPPING';
    InstanceService.stopInstance(instance);
  };

  $scope.successCallback = function(response) {
    $rootScope.systems = response.data;
    $scope.systems.loaded = true;
    $scope.systems.error = false;
    $scope.systems.status = response.status;
    $scope.systems.errorMessage = '';

    $scope.systems.data = _.groupBy(response.data, function(value) {
      return value.display_name || value.name;
    });

    // Extra kick for the 'empty' directive
    if (Object.keys($scope.systems.data).length === 0) {
      $scope.systems.status = 404;
    }
  };

  $scope.failureCallback = function(response) {
    $scope.systems.data = [];
    $scope.systems.loaded = false;
    $scope.systems.error = true;
    $scope.systems.status = response.status;
    $scope.systems.errorMessage = response.data.message;
  };

  let socketConnection = undefined;

  /**
   * websocketConnect - Open a websocket connection.
   */
  function websocketConnect() {
    if (window.WebSocket && !socketConnection) {
      let proto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
      let eventUrl = proto + window.location.host + '/api/v1/socket/events';

      let token = localStorageService.get('token');
      if (token) {
        eventUrl += '?token=' + token;
      }

      socketConnection = $websocket(eventUrl);

      socketConnection.onClose((message) => {
        console.log('Websocket closed: ' + message.reason);
      });
      socketConnection.onError((message) => {
        console.log('Websocket error: ' + message.reason);
      });
      socketConnection.onMessage((message) => {
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

      $scope.$on('destroy', function() {
        if (angular.isDefined(socketConnection)) {
          socketConnection.close();
          socketConnection = undefined;
        }
      });
    }
  }

  /**
   * updateInstanceStatus - Change the status of an instance
   * @param {string} id  The instance ID
   * @param {string} newStatus  The new status
   */
  function updateInstanceStatus(id, newStatus) {
    if (newStatus === undefined) return;

    for (let systemName in $scope.systems.data) {
      if ({}.hasOwnProperty.call($scope.systems.data, systemName)) {
        for (let system of $scope.systems.data[systemName]) {
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
    for (let systemName in $scope.systems.data) {
      if ({}.hasOwnProperty.call($scope.systems.data, systemName)) {
        for (let system of $scope.systems.data[systemName]) {
          if (system.id === id) {
            _.pull($scope.systems.data[systemName], system);

            if ($scope.systems.data[systemName].length === 0) {
              delete $scope.systems.data[systemName];
            }
          }
        }
      }
    }
  }

  let loadSystems = function() {
    SystemService.getSystems(true, 'id,name,display_name,version,instances')
      .then($scope.successCallback, $scope.failureCallback);
  };

  // Periodically poll for changes (in case of websocket failure)
  let systemsUpdate = $interval(function() {
    loadSystems();
  }, 5000);
  $scope.$on('$destroy', function() {
    if (angular.isDefined(systemsUpdate)) {
      $interval.cancel(systemsUpdate);
      systemsUpdate = undefined;
    }
  });

  let loadAll = function() {
    loadSystems();
    websocketConnect();
  };

  $scope.$on('userChange', function() {
    loadAll();
  });

  loadAll();
};
