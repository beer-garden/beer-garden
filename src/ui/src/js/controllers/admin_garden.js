import _ from 'lodash';

adminGardenController.$inject = [
  '$scope',
  '$rootScope',
  'GardenService',
  'EventService',
];

/**
 * adminGardenController - Garden management controller.
 * @param  {Object} $scope          Angular's $scope object.
 * @param  {Object} $rootScope      Angular's $rootScope object.
 * @param  {Object} GardenService    Beer-Garden's garden service object.
 * @param  {Object} EventService    Beer-Garden's event service object.
 */
export default function adminGardenController(
    $scope,
    $rootScope,
    GardenService,
    EventService) {
  $scope.setWindowTitle('gardens');

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

  let loadAll = function() {
    $scope.response = undefined;
    $scope.data = [];
    $scope.alerts = [];
  };

  EventService.addCallback('admin_system', (event) => {
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

  // if ($rootScope.sysResponse.status == 200) {
  //   $scope.successCallback($rootScope.sysResponse);
  // } else {
  //   $scope.failureCallback($rootScope.sysResponse);
  // }

  $scope.$on('userChange', function() {
    loadAll();
  });

  loadAll();
};
