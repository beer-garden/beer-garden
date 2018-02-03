import angular from 'angular';

systemViewController.$inject = ['$scope', '$stateParams', '$interval', 'SystemService', 'CommandService', 'UtilityService', 'DTOptionsBuilder'];
export default function systemViewController($scope, $stateParams, $interval, SystemService, CommandService, UtilityService, DTOptionsBuilder) {
  $scope.util = UtilityService;

  $scope.system = {
    data: {},
    loaded: false,
    error: false,
    errorMessage: '',
    forceReload: false,
    status: null,
    errorMap: {
      'empty' : {
        'solutions' : [
          {
            problem     : 'ID is incorrect',
            description : 'The Backend has restarted and the ID changed of the system you were looking at',
            resolution  : 'Click the ' + $scope.config.application_name + ' logo at the top left and refresh the page'
          },
          {
            problem     : 'The Plugin Stopped',
            description : 'The plugin could have been stopped. You should probably contact the plugin ' +
                          'maintainer. You should be able to tell what\'s wrong by their logs. Plugins ' +
                          'are located at <code>$APP_HOME/plugins</code>',
            resolution  : '<kbd>less $APP_HOME/log/my-plugin.log</kbd>'
          }
        ]
      }
    }
  };

  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('order', [4, 'asc'])
    .withOption('autoWidth', false)
    .withBootstrap();

  $scope.successCallback = function(response) {
    $scope.system.data = response.data;
    $scope.system.loaded = true;
    $scope.system.error = false;
    $scope.system.status = response.status;
    $scope.system.errorMessage = '';
  }

  $scope.failureCallback = function(response) {
    $scope.system.data = {};
    $scope.system.loaded = false;
    $scope.system.error = true;
    $scope.system.status = response.status;
    $scope.system.errorMessage = data.message;
  }

  // Register a function that polls if the system is in a transition status
  var status_update = $interval(function() {
    if(['STOPPING', 'STARTING'].indexOf($scope.system.data.status) != -1) {
      SystemService.getSystem($scope.system.data.id, false, function(data, status, headers, config) {
        $scope.system.data.status = data.status;
      });
    }
  }, 1000);

  $scope.$on('$destroy', function() {
    if(angular.isDefined(status_update)) {
      $interval.cancel(status_update);
      status_update = undefined;
    }
  });

  SystemService.getSystem($stateParams.id, true)
    .then($scope.successCallback, $scope.failureCallback);
};
