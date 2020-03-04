import _ from 'lodash';

adminGardenController.$inject = [
  '$scope',
  'GardenService',
  'EventService',
];

/**
 * adminGardenController - Garden management controller.
 * @param  {Object} $scope          Angular's $scope object.
 * @param  {Object} GardenService    Beer-Garden's garden service object.
 * @param  {Object} EventService    Beer-Garden's event service object.
 */
export default function adminGardenController(
    $scope,
    GardenService,
    EventService) {
  $scope.setWindowTitle('gardens');

  $scope.successCallback = function(response) {
    $scope.response = response;

  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = [];
  };

  let loadGardens = function() {
    GardenService.getGardens().then(
      $scope.successCallback,
      $scope.failureCallback
    );
  };

  let loadAll = function() {
    $scope.response = undefined;
    $scope.data = [];

    loadGardens();
  };

  EventService.addCallback('admin_system', (event) => {
    switch (event.name) {
      case 'GARDEN_CREATED':
        break;
      case 'GARDEN_REMOVED':
        break;
    }
  });

  $scope.$on('userChange', function() {
    loadAll();
  });

  loadAll();
};
