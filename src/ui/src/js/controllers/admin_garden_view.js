import _ from 'lodash';

adminGardenViewController.$inject = [
  '$scope',
  'GardenService',
  'EventService',
  'garden'
];

/**
 * adminGardenController - Garden management controller.
 * @param  {Object} $scope          Angular's $scope object.
 * @param  {Object} GardenService    Beer-Garden's garden service object.
 * @param  {Object} EventService    Beer-Garden's event service object.
 */
export default function adminGardenViewController(
    $scope,
    GardenService,
    EventService,
    garden) {
  $scope.setWindowTitle('edit garden');

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;

  };
 $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = [];
  };

  let loadGarden = function() {
    GardenService.getGarden($scope.garden).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  };

  $scope.successCallback(garden);
  };