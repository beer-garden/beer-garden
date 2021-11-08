import { formatJsonDisplay } from "../../services/utility_service.js";

jobCreateTriggerController.$inject = [
  "$scope",
  "$state",
  "$stateParams",
  "JobService",
];

/**
 * jobCreateController - Controller for the job create page.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $state            Angular's $state object.
 * @param  {Object} $stateParams      Angular's $stateParams object.
 * @param  {Object} JobService        Beer-Garden's job service.
 */
export default function jobCreateTriggerController(
  $scope,
  $state,
  $stateParams,
  JobService
) {
  $scope.setWindowTitle("scheduler");

  $scope.alerts = [];

  $scope.schema = JobService.SCHEMA;
  $scope.form = JobService.FORM;
  $scope.request = $stateParams.request;

  if ($stateParams.job == null) {
    $scope.model = {};
  } else {
    $scope.model = JobService.serverModelToForm($stateParams.job);
  }

  let generateJobSF = function () {
    $scope.$broadcast("schemaFormRedraw");
  };

  const extraValidate = function (model) {
    let triggerType = model["trigger_type"];
    let valid = true;
    if (!angular.isDefined(triggerType) || triggerType === null) {
      return false;
    }

    for (let key of JobService.getRequiredKeys(triggerType)) {
      if (!angular.isDefined(model[key]) || model[key] === null) {
        $scope.alerts.push("Missing required key: " + key);
        valid = false;
      }
    }

    if (triggerType === "interval") {
      if (
        ((angular.isDefined(model["interval_start_date"]) &&
          model["interval_start_date"] !== null) ||
          (angular.isDefined(model["interval_end_date"]) &&
            model["interval_end_date"] !== null)) &&
        (!angular.isDefined(model["interval_timezone"]) ||
          model["interval_timezone"] === null)
      ) {
        $scope.alerts.push(
          "If a date is specified, you must specify the timezone."
        );
        valid = false;
      }
    }

    if (triggerType === "cron") {
      if (
        ((angular.isDefined(model["cron_start_date"]) &&
          model["cron_start_date"] !== null) ||
          (angular.isDefined(model["cron_end_date"]) &&
            model["cron_end_date"] !== null)) &&
        (!angular.isDefined(model["cron_timezone"]) ||
          model["cron_timezone"] === null)
      ) {
        $scope.alerts.push(
          "If a date is specified, you must specify the timezone."
        );
        valid = false;
      }
    }

    if (triggerType === "file") {
      if (
        angular.isDefined(model["file_pattern"]) &&
        model["file_pattern"] === [""]
      ) {
        $scope.alerts.push("At least one pattern is required.");
        valid = false;
      }
      if (
        angular.isDefined(model["file_callbacks"]) &&
        model["file_callbacks"] !== null
      ) {
        var temp = false;
        for (var k in model["file_callbacks"]) {
          if (model["file_callbacks"][k] == true) temp = true;
        }
        if (!temp) {
          $scope.alerts.push("At least one callback is required.");
          valid = temp;
        }
      }
    }

    return valid;
  };

  // These are shared with create_request
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
    $scope.alerts.splice(0);

    $scope.$broadcast("schemaFormValidate");

    let valid = extraValidate(model);

    if (form.$valid && valid) {
      let serverModel = JobService.formToServerModel(model, $scope.request);

      JobService.createJob(serverModel).then(
        function (response) {
          $state.go("base.job", { id: response.data.id });
        },
        function (response) {
          $scope.createResponse = response;
        }
      );
    } else {
      $scope.alerts.push(
        "Looks like there was an error validating the request."
      );
    }
  };

  $scope.reset = function (form, model, system, command) {
    $scope.createResponse = undefined;
    $scope.alerts.splice(0);
    if ($stateParams.job == null) {
      $scope.model = {};
    } else {
      $scope.model = JobService.serverModelToForm($stateParams.job);
    }
    generateJobSF();
    form.$setPristine();
  };

  generateJobSF();
}
