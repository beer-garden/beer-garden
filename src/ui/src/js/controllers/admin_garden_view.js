import _ from "lodash";

adminGardenViewController.$inject = [
  "$scope",
  "GardenService",
  "EventService",
  "$stateParams",
];

/**
 * adminGardenController - Garden management controller.
 * @param  {Object} $scope          Angular's $scope object.
 * @param  {Object} GardenService    Beer-Garden's garden service object.
 */
export default function adminGardenViewController(
  $scope,
  GardenService,
  EventService,
  $stateParams
) {
  $scope.setWindowTitle("Configure Garden");
  $scope.alerts = [];

  $scope.isLocal = false;
  $scope.gardenSchema = null;
  $scope.gardenForm = null;
  $scope.gardenModel = {};

  $scope.closeAlert = function (index) {
    $scope.alerts.splice(index, 1);
  };

  let generateGardenSF = function () {
    $scope.gardenSchema = GardenService.SCHEMA;
    $scope.gardenForm = GardenService.FORM;
    $scope.gardenModel = GardenService.serverModelToForm($scope.data);

    $scope.$broadcast("schemaFormRedraw");
  };

  $scope.successCallback = function (response) {
    $scope.response = response;
    $scope.data = response.data;

    if ($scope.data.id == null || $scope.data.connection_type == "LOCAL") {
      $scope.isLocal = true;
      $scope.alerts.push({
        type: "info",
        msg: "Since this is the local Garden it's not possible to modify connection information",
      });
    }

    generateGardenSF();
  };

  $scope.failureCallback = function (response) {
    $scope.response = response;
    $scope.data = [];
  };

  let loadGarden = function () {
    GardenService.getGarden($stateParams.name).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  };

  let loadAll = function () {
    $scope.response = undefined;
    $scope.data = [];

    loadGarden();
  };

  $scope.addErrorAlert = function (response) {
    $scope.alerts.push({
      type: "danger",
      msg:
        "Something went wrong on the backend: " +
        _.get(response, "data.message", "Please check the server logs"),
    });
  };

  $scope.submitGardenForm = function (form, model) {
    $scope.$broadcast("schemaFormValidate");

    if (form.$valid) {
      let updated_garden = GardenService.formToServerModel($scope.data, model);

      GardenService.updateGardenConfig(updated_garden).then(
        _.noop,
        $scope.addErrorAlert
      );
    } else {
      $scope.alerts.push(
        "Looks like there was an error validating the Garden."
      );
    }
  };

  $scope.syncGarden = function () {
    GardenService.syncGarden($scope.data.name);
  };

  EventService.addCallback("admin_garden_view", (event) => {
    switch (event.name) {
      case "GARDEN_UPDATED":
        if ($scope.data.id == event.payload.id) {
          $scope.data = event.payload;
        }
        break;
    }
  });

  $scope.$on("$destroy", function () {
    EventService.removeCallback("admin_garden_view");
  });

  $scope.$on("userChange", function () {
    loadAll();
  });

  loadAll();
}
