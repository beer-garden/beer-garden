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
    EventService,
) {
  $scope.setWindowTitle('gardens');
  $scope.alerts = [];
  $scope.gardenCreateSchema = GardenService.CreateSCHEMA;
  $scope.gardenCreateForm = GardenService.CreateFORM;
  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;
  };
  $scope.garden_name = null;
  $scope.createGardenFormHide = true;
  $scope.create_garden_name = null;
  $scope.createGardenFormHide = true;
  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = [];
  };
  $scope.is_unique_garden_name = true;
  $scope.create_garden_popover_message = null;
  $scope.create_garden_name_focus = false;

  const loadGardens = function() {
    GardenService.getGardens().then(
        $scope.successCallback,
        $scope.failureCallback,
    );
  };

  $scope.syncGardens = function() {
    GardenService.syncGardens().then((resp)=>{
      $scope.alerts.push({
        type: 'success',
        msg: 'Server accepted request to sync all gardens',
      });
    }).catch((err) => {
      if (err.data && err.data.message) {
        $scope.alerts.push({
          type: 'danger',
          msg: err.data.message,
        });
        console.log('error', err.data.message);
      }
    });
  };

  $scope.closeCreateGardenForm = function() {
    $scope.createGardenFormHide = true;
    $scope.create_garden_name = null;
  };

  $scope.checkForGardenDuplication = function() {
    $scope.is_unique_garden_name = true;
    $scope.create_garden_popover_message = null;
    $scope.create_garden_popover_active = false;
    for (let i = 0; i < $scope.data.length; i++) {
      if ($scope.data[i].name == $scope.create_garden_name) {
        $scope.is_unique_garden_name = false;
        $scope.create_garden_popover_message = 'Garden name is already in use.';
        break;
      }
    }
  };

  $scope.createGarden = function() {
    if ($scope.is_unique_garden_name) {
      GardenService.createGarden({
        name: $scope.create_garden_name,
        status: 'NOT_CONFIGURED',
      });
      $state.go('base.garden_view', {
        name: $scope.create_garden_name,
      });
    }
  };

  $scope.editGarden = function(garden) {
    $state.go('base.garden_view', {
      name: garden.name,
    });
  };

  $scope.deleteGarden = function(garden) {
    GardenService.deleteGarden(garden);
  };

  const loadAll = function() {
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
        for (let i = 0; i < $scope.data.length; i++) {
          if ($scope.data[i].id == event.payload.id) {
            $scope.data.splice(i, 1);
          }
        }
        break;
      case 'GARDEN_UPDATED':
        for (let i = 0; i < $scope.data.length; i++) {
          if ($scope.data[i].id == event.payload.id) {
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
}
