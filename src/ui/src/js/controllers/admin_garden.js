import _ from 'lodash';

adminGardenController.$inject = [
  '$scope',
  '$state',
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
    $state,
    GardenService,
    EventService) {
  $scope.setWindowTitle('gardens');
  $scope.gardenCreateSchema = GardenService.CreateSCHEMA;
   $scope.gardenCreateForm = GardenService.CreateFORM;
  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;

  };
  $scope.garden_name = null;
  $scope.createGardenFormHide = true;
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

  $scope.syncGardens = function() {
    GardenService.syncGardens()
  }

  $scope.createGarden = function() {
      if ($scope.garden_name != "" & $scope.garden_name != null){
        GardenService.createGarden({"name":$scope.garden_name, "status":"NOT_CONFIGURED"});
        $state.go('base.garden_view',
              {
                'name': $scope.garden_name,
              }
            );
      }
      $scope.createGardenFormHide = true;

  }

  $scope.editGarden = function(garden) {
    $state.go('base.garden_view',
      {
        'name': garden.name,
      }
    );
  };

  $scope.deleteGarden = function(garden) {
    GardenService.deleteGarden(garden)
  };

  let loadAll = function() {
    $scope.response = undefined;
    $scope.data = [];

    loadGardens();
  };

  EventService.addCallback('admin_garden', (event) => {
    switch (event.name) {
      case 'GARDEN_CREATED':
        $scope.data.push(event.payload);
        break;
      case 'GARDEN_REMOVED':
        for (var i = 0; i < $scope.data.length; i++) {
            if ($scope.data[i].id == event.payload.id){
                $scope.data.splice(i, 1)
            }
        }
        break;
      case 'GARDEN_UPDATED':
        for (var i = 0; i < $scope.data.length; i++) {
            if ($scope.data[i].id == event.payload.id){
                $scope.data[i] = event.payload;
            }
        }
        break;
    }
  });

  $scope.$on('$destroy', function() {
    EventService.removeCallback('admin_garden');
  });

  $scope.$on('userChange', function() {
    loadAll();
  });

  loadAll();
};
