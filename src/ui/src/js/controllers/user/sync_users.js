import _ from 'lodash';

syncUsersController.$inject = [
  '$scope',
  '$uibModalInstance',
  'EventService',
  'GardenService',
];

/**
 * syncUsersController - Sync Users controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 * @param  {Object} EventService                  Beer-Garden's event service.
 * @param  {Object} GardenService                 Beer-Garden's garden service.
 */
export default function syncUsersController(
    $scope,
    $uibModalInstance,
    EventService,
    GardenService,
) {
  $scope.gardens = [];

  $scope.sync = function() {
    $scope.gardens.forEach((garden) => {
      if (garden.status === 'RUNNING') {
        garden.syncStatus = 'IN_PROGRESS';
      }
    });

    GardenService.syncUsers();
  };

  $scope.cancel = function() {
    $uibModalInstance.close();
  };

  $scope.disableSubmit = function() {
    return (
      _.filter($scope.gardens, function(garden) {
        return garden.syncStatus === 'IN_PROGRESS';
      }).length > 0
    );
  };

  EventService.addCallback('sync_users', (event) => {
    if (event.name === 'USERS_IMPORTED') {
      $scope.$apply(() => {
        handleUsersImportedEvent(event);
      });
    }
  });

  $scope.$on('$destroy', function() {
    EventService.removeCallback('sync_users');
  });

  const handleUsersImportedEvent = function(event) {
    $scope.gardens.forEach((garden) => {
      if (garden.name === event.metadata.garden) {
        garden.syncStatus = 'COMPLETE';
      }
    });
  };

  const successCallback = function(response) {
    $scope.response = response;
    $scope.gardens = [];

    response.data.forEach((garden) => {
      if (garden.connection_type !== 'LOCAL') {
        if (garden.status !== 'RUNNING') {
          garden.syncStatus = 'NOT RUNNING';
        } else {
          garden.syncStatus = 'PENDING';
        }

        $scope.gardens.push(garden);
      }
    });
  };

  const failureCallback = function(response) {
    $scope.response = response;
    $scope.gardens = [];
  };

  const loadGardens = function() {
    GardenService.getGardens().then(successCallback, failureCallback);
  };

  loadGardens();
}
