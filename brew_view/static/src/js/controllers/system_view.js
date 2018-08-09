import _ from 'lodash';

systemViewController.$inject = [
  '$rootScope',
  '$scope',
  '$stateParams',
  '$interval',
  'SystemService',
  'UtilityService',
  'DTOptionsBuilder',
];

/**
 * systemViewController - Angular Controller for viewing a single system.
 * @param  {$rootScope} $rootScope     Angular's $rootScope object.
 * @param  {$scope} $scope             Angular's $scope object.
 * @param  {$stateParams} $stateParams Angular's $stateParams object.
 * @param  {$interval} $interval       Angular's $interval object.
 * @param  {Object} SystemService      Beer-Garden System Service.
 * @param  {Object} UtilityService     Beer-Garden Utility Service.
 * @param  {Object} DTOptionsBuilder   Object for building Data-Tables objects.
 */
export default function systemViewController(
  $rootScope,
  $scope,
  $stateParams,
  $interval,
  SystemService,
  UtilityService,
  DTOptionsBuilder) {
  $scope.util = UtilityService;

  $scope.system = {
    data: {},
    loaded: false,
    error: false,
    errorMessage: '',
    forceReload: false,
    status: null,
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
  };

  $scope.failureCallback = function(response) {
    $scope.system.data = {};
    $scope.system.loaded = false;
    $scope.system.error = true;
    $scope.system.status = response.status;
    $scope.system.errorMessage = response.data.message;
  };

  // Register a function that polls if the system is in a transition status
  let statusUpdate = $interval(function() {
    if (['STOPPING', 'STARTING'].indexOf($scope.system.data.status) != -1) {
      SystemService.getSystem(
        $scope.system.data.id, false,
        function(data, status, headers, config) {
          $scope.system.data.status = data.status;
      });
    }
  }, 1000);

  $scope.$on('$destroy', function() {
    if (angular.isDefined(statusUpdate)) {
      $interval.cancel(statusUpdate);
      statusUpdate = undefined;
    }
  });

  /**
   * Get the state params required for the $stateProvider to route this command.
   *
   * @param {Object} command - command from server.
   * @return {Object} params for routing.
   */
  $scope.getCommandStateParams = function(command) {
    return {
      systemName: $scope.system.data.name,
      systemVersion: $rootScope.getVersionForUrl($scope.system.data),
      name: command.name,
      id: command.id,
    };
  };

  const loadSystem = function(stateParams) {
    if (_.isUndefined(stateParams.id)) {
      $rootScope.findSystem($stateParams.name, $stateParams.version).then(
        (system) => {
          SystemService.getSystem(system.id, true).then(
            $scope.successCallback,
            $scope.failureCallback
          );
        },
        $scope.failureCallback
      );
    } else {
      SystemService.getSystem(stateParams.id, true).then(
        $scope.successCallback,
        $scope.failureCallback
      );
    }
  };

  $scope.$on('userChange', function() {
    loadSystem($stateParams);
  });

  loadSystem($stateParams);
};
