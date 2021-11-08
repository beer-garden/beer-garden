import { formatJsonDisplay } from "../../services/utility_service.js";

jobCreateRequestController.$inject = [
  "$scope",
  "$state",
  "$stateParams",
  "SFBuilderService",
  "SystemService",
];

/**
 * jobCreateRequestController - Controller for the job create page.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $state            Angular's $state object.
 * @param  {Object} $stateParams      Angular's $stateParams object.
 * @param  {Object} SFBuilderService  Beer-Garden's schema-form service.
 * @param  {Object} SystemService   Beer-Garden's system service object.
 */
export default function jobCreateRequestController(
  $scope,
  $state,
  $stateParams,
  SFBuilderService,
  SystemService
) {
  $scope.setWindowTitle("scheduler");

  $scope.alerts = [];

  $scope.schema = null;
  $scope.form = null;
  $scope.model = {};
  $scope.job = null;

  if ($stateParams.job == null) {
    $scope.system = $stateParams.system;
    $scope.command = $stateParams.command;
  } else {
    $scope.system = SystemService.findSystem(
      $stateParams.job.request_template.namespace,
      $stateParams.job.request_template.system,
      $stateParams.job.request_template.system_version
    );

    for (let i in $scope.system.commands) {
      if (
        $scope.system.commands[i].name ==
        $stateParams.job.request_template.command
      ) {
        $scope.command = $scope.system.commands[i];
        break;
      }
    }

    $scope.job = $stateParams.job;

    //Clone to allow resets
    $scope.model = _.cloneDeep($scope.job.request_template);
    $scope.modelJson = angular.toJson($scope.model, 2);
  }

  let generateRequestSF = function () {
    let sf = SFBuilderService.build($scope.system, $scope.command);

    $scope.schema = sf["schema"];
    $scope.form = sf["form"];

    $scope.$broadcast("schemaFormRedraw");
  };

  // These are shared with create_trigger
  $scope.loadPreview = function (_editor) {
    formatJsonDisplay(_editor, true);
  };
  $scope.closeAlert = function (index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.$watch(
    "model",
    function (val, old) {
      if (val && val !== old) {
        if ($scope.system["display_name"]) {
          val["system"] = $scope.system["display_name"];
        }

        try {
          $scope.modelJson = angular.toJson(val, 2);
        } catch (e) {
          console.error("Error attempting to stringify the model");
        }
      }
    },
    true
  );

  $scope.submit = function (form, model) {
    // Remove all the old alerts so they don't just stack up
    $scope.alerts.splice(0);

    // Give all the fields the chance to validate
    $scope.$broadcast("schemaFormValidate");

    // This is gross, but tv4 does not handle arrays well and throws errors
    // where it shouldn't. I don't think it's possible to fix without a patch
    // to tv4 or ASF so for now just ignore the false positive.
    let valid = true;
    if (!form.$valid) {
      angular.forEach(form.$error, function (errorGroup, errorKey) {
        if (errorKey !== "schemaForm") {
          angular.forEach(errorGroup, function (error) {
            if (errorKey !== "tv4-0" || !Array.isArray(error.$modelValue)) {
              valid = false;
            }
          });
        }
      });
    }

    if (valid) {
      let newRequest = angular.copy($scope.model);

      if (
        $scope.system["display_name"] &&
        $scope.system["display_name"] === newRequest["system"]
      ) {
        newRequest["system"] = $scope.system["name"];
        newRequest["metadata"] = {
          system_display_name: $scope.system["display_name"],
        };
      }

      $state.go("base.jobscreatetrigger", {
        job: $scope.job,
        request: newRequest,
      });
    } else {
      $scope.alerts.push(
        "Looks like there was an error validating the request."
      );
    }
  };

  $scope.reset = function (form, model, system, command) {
    $scope.alerts.splice(0);

    if ($scope.job == null) {
      $scope.model = {};
    } else {
      $scope.model = _.cloneDeep($scope.job.request_template);
      $scope.modelJson = angular.toJson($scope.model, 2);
    }

    generateRequestSF();
    form.$setPristine();
  };

  generateRequestSF();
}
