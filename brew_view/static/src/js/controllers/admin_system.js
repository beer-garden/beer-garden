import angular from 'angular';
import _ from 'lodash';

systemAdminController.$inject = [
  '$scope',
  '$rootScope',
  '$interval',
  '$http',
  '$websocket',
  'SystemService',
  'InstanceService',
  'UtilityService',
  'AdminService',
];

/**
 * systemAdminController - System management controller.
 * @param  {$scope} $scope          Angular's $scope object.
 * @param  {$rootScope} $rootScope  Angular's $rootScope object.
 * @param  {$interval} $interval    Angular's $interval object.
 * @param  {$http} $http            Angular's $http object.
 * @param  {$websocket} $websocket  Angular's $websocket object.
 * @param  {Object} SystemService   Beer-Garden's system service object.
 * @param  {Object} InstanceService Beer-Garden's instance service object.
 * @param  {Object} UtilityService  Beer-Garden's utility service object.
 * @param  {Object} AdminService    Beer-Garden's admin service object.
 */
export default function systemAdminController(
    $scope,
    $rootScope,
    $interval,
    $http,
    $websocket,
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

  let socketError = false;

  function websocketConnect() {
    if (window.WebSocket && !socketError) {
      let proto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
      let event_url = proto + window.location.host + '/api/v1/socket/events';

      let socketConnection = $websocket(event_url);
      socketConnection.onMessage(handleWebsocketMessage);

      // If the connection is broken attempt to reconnect.
      // If this is caused by brew-view stopping the reconnect attempt will
      // probably error. This isn't ideal, but we can't distinguish between a
      // 'real' error and brew-view being down, so we live with this for now.
      socketConnection.onClose(websocketConnect);
      socketConnection.onError(function() {
        socketError = true;
      });

      $scope.$on('destroy', function() {
        if (angular.isDefined(socketConnection)) {
          socketConnection.close();
          socketConnection = undefined;
        }
      });
    }
  }

  function handleWebsocketMessage(message) {
    let event = JSON.parse(message.data);
    console.log(event);

    switch(event.name) {
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
  }

  function updateInstanceStatus(id, newStatus) {
    if (newStatus === undefined) return;

    for (let system_name in $scope.systems.data) {
      for (let system of $scope.systems.data[system_name]) {
        for (let instance of system.instances) {
          if (instance.id === id) {
            instance.status = newStatus;
          }
        }
      }
    }
  }

  function removeSystem(id) {
    for (let system_name in $scope.systems.data) {
      for (let system of $scope.systems.data[system_name]) {
        if (system.id === id) {
          _.pull($scope.systems.data[system_name], system);

          if ($scope.systems.data[system_name].length === 0) {
            delete $scope.systems.data[system_name];
          }
        }
      }
    }
  }

  // Attempt to connect to the event websocket
  websocketConnect();

  // Register a function that polls for systems...
  let systemsUpdate = $interval(function() {
    SystemService.getSystems().then($scope.successCallback,
                                    $scope.failureCallback);
  }, 5000);
  $scope.$on('$destroy', function() {
    if (angular.isDefined(systemsUpdate)) {
      $interval.cancel(systemsUpdate);
      systemsUpdate = undefined;
    }
  });

  // ...but go immediately so we don't have to wait for first interval
  SystemService.getSystems().then($scope.successCallback,
                                  $scope.failureCallback);
};
