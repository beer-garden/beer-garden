import _ from 'lodash';

adminGardenViewController.$inject = [
  '$scope',
  'GardenService',
  'EventService',
  '$stateParams'
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
    $stateParams) {
  $scope.setWindowTitle('Configure Garden');

  $scope.gardenSchema = null;
  $scope.gardenForm = null;
  $scope.gardenModel = {};

  let generateGardenSF = function() {
    $scope.gardenSchema = GardenService.SCHEMA;
    $scope.gardenForm = GardenService.FORM;
    $scope.gardenModel = GardenService.serverModelToForm($scope.data);
    $scope.$broadcast('schemaFormRedraw');
  };
  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;
    $scope.gardenModel = response.data;
    generateGardenSF();

  };
 $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = [];
  };

  let loadGarden = function() {
    GardenService.getGarden($stateParams.name).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  };

  let loadAll = function() {
    $scope.response = undefined;
    $scope.data = [];

    loadGarden();
  };

  $scope.submitGardenForm = function(form, model) {
    $scope.$broadcast('schemaFormValidate');

    if (form.$valid){
       var garden = GardenService.formToServerModel($scope.data, model);
       GardenService.updateGardenConfig(garden);

     }
  };

  $scope.$on('userChange', function() {
    loadAll();
  });

  loadAll();

  };