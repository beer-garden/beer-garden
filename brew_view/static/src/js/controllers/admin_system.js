import angular from 'angular';

systemAdminController.$inject = ['$scope', '$rootScope', '$interval', '$http', 'SystemService', 'InstanceService', 'UtilityService', 'AdminService'];
export default function systemAdminController($scope, $rootScope, $interval, $http, SystemService, InstanceService, UtilityService, AdminService) {
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
        'solutions' : [
          {
            problem     : 'Backend Down',
            description : 'If the backend is down, there will be no systems to control',
            resolution  : '<kbd>service bartender start</kbd>'
          },
          {
            problem     : 'Plugin Problems',
            description : 'If Plugins attempted to start, but are failing to startup, then' +
                          'you\'ll have to contact the plugin maintainer. You can tell what\'s wrong ' +
                          'by their logs. Plugins are located at <code>$APP_HOME/plugins</code>',
            resolution  : '<kbd>less $APP_HOME/log/my-plugin.log</kbd>'
          },
          {
            problem     : 'Database Names Do Not Match',
            description : 'It is possible that the backend is pointing to a Different Database than ' +
                          'the Frontend. Check to make sure that the <code>DB_NAME</code> in both ' +
                          'config files is the same',
            resolution  : '<kbd>vim $APP_HOME/conf/bartender.json</kbd><br />' +
                          '<kbd>vim $APP_HOME/conf/brew-view.json</kbd>'
          },
          {
            problem     : 'There Are No Systems',
            description : 'If no one has ever developed any plugins, then there will be no systems ' +
                          'here. You\'ll need to build your own plugins.',
            resolution  : 'Develop a Plugin'
          }
        ]
      }
    }
  };

  $scope.rescan = function() {
    AdminService.rescan();
  };

  $scope.startSystem = function(system) {
    for(var i=0; i<system.instances.length; i++) {
      system.instances[i].status = 'STARTING';
      InstanceService.startInstance(system.instances[i]);
    }
  };

  $scope.stopSystem = function(system) {
    for(var i=0; i<system.instances.length; i++) {
      system.instances[i].status = 'STOPPING';
      InstanceService.stopInstance(system.instances[i]);
    }
  };

  $scope.reloadSystem = function(system) {
    system.status = 'RELOADING';
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

  // Register a function that polls for system status
  var status_update = $interval(function() {
    SystemService.getSystems().then($scope.successCallback, $scope.failureCallback);
  }, 5000);

  $scope.$on('$destroy', function() {
    if(angular.isDefined(status_update)) {
      $interval.cancel(status_update);
      status_update = undefined;
    }
  });

  var groupSystems = function(rawSystems) {
    var systems = {};
    for(var i=0; i<rawSystems.length; i++) {
      var system = rawSystems[i];
      var systemName = system.display_name || system.name;
      if(!(systemName in systems)) {
        systems[systemName] = {};
      }
      systems[systemName][system.version] = system;
    }
    return systems;
  };

  $scope.successCallback = function(response) {
    $rootScope.systems = response.data;
    $scope.systems.loaded = true;
    $scope.systems.error = false;
    $scope.systems.status = response.status;
    $scope.systems.errorMessage = '';

    $scope.systems.data = groupSystems(response.data);

    // Extra kick for the 'empty' directive
    if(Object.keys($scope.systems.data).length === 0) {
      $scope.systems.status = 404;
    }
  }

  $scope.failureCallback = function(response) {
    $scope.systems.data = [];
    $scope.systems.loaded = false;
    $scope.systems.error = true;
    $scope.systems.status = response.status;
    $scope.systems.errorMessage = response.data.message;
  }

  SystemService.getSystems().then($scope.successCallback, $scope.failureCallback);
};
