import { formatDate, formatJsonDisplay } from "../services/utility_service.js";
import modalTemplate from "../../templates/reset_interval_modal.html";

jobViewController.$inject = [
  "$scope",
  "$rootScope",
  "$state",
  "$stateParams",
  "$uibModal",
  "JobService",
];

/**
 * jobViewController - Controller for the job view page.
 * @param  {Object} $scope        Angular's $scope object.
 * @param  {Object} $rootScope    Angular's $rootScope object.
 * @param  {Object} $state        Angular's $state object.
 * @param  {Object} $stateParams  Angular's $stateParams object.
 * @param  {Object} $uibModal     Angular UI's $uibModal object.
 * @param  {Object} JobService    Beer-Garden's job service.
 */
export function jobViewController(
  $scope,
  $rootScope,
  $state,
  $stateParams,
  $uibModal,
  JobService
) {
  $scope.setWindowTitle("scheduler");

  $scope.formattedRequestTemplate = "";
  $scope.formattedTrigger = "";

  $scope.loadPreview = function (_editor) {
    formatJsonDisplay(_editor, true);
  };

  $scope.formatDate = formatDate;

  $scope.successCallback = function (response) {
    $scope.response = response;
    $scope.data = response.data;

    $scope.formattedRequestTemplate = JSON.stringify(
      $scope.data.request_template,
      undefined,
      2
    );
    $scope.formattedTrigger = JSON.stringify($scope.data.trigger, undefined, 2);
  };

  $scope.resumeJob = function (jobId) {
    JobService.resumeJob(jobId).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  };

  $scope.pauseJob = function (jobId) {
    JobService.pauseJob(jobId).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  };

  $scope.updateJob = function (job) {
    $state.go("base.jobscreaterequest", { job: job });
  };

  $scope.deleteJob = function (jobId) {
    JobService.deleteJob(jobId).then(
      $state.go("base.jobs"),
      $scope.failureCallback
    );
  };

  $scope.failureCallback = function (response) {
    $scope.response = response;
    $scope.data = [];
  };

  function loadJob() {
    $scope.response = undefined;
    $scope.data = [];

    JobService.getJob($stateParams.id).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  }

  $scope.$on("userChange", () => {
    loadJob();
  });

  /*
   * Execute the job service's "run ad hoc job" functionality.
   */
  function runAdHoc(jobId) {
    const resettingInterval = $scope.resetTheInterval;

    JobService.runAdHocJob(jobId, $scope.resetTheInterval).then(
      function (response) {
        console.log(`Ad hoc run of ID ${jobId}; reset interval: ${resettingInterval}`);
        $state.go("base.jobs");
      },
      function (response) {
        alert("Failure! Server returned status " + response.status);
      }
    );
  }

  /*
   * This is a stub: will be
   *
   *   return triggerType === "interval";
   *
   * when the BG API can make sense of a reset interval value
   */
  function isIntervalTrigger(triggerType) {
    return true;
  }

  /*
   * Schedule a job to be run immediately.
   */
  $scope.runJobNow = function (jobData) {
    $scope.resetTheInterval = false;

    let theTriggerIsInterval = isIntervalTrigger(jobData["trigger_type"]);
    let jobId = jobData["id"];

    if (theTriggerIsInterval) {
      // open modal dialog to update resetTheInterval
      let popupInstance = $uibModal.open({
        animation: true,
        template: modalTemplate,
        controller: "JobRunNowModalController"
      });

      popupInstance.result.then(
        function (result) {
          $scope.resetTheInterval = result;
          runAdHoc(jobId);
        },
        () => console.log("Ad hoc run cancelled")
      );
    } else {
      runAdHoc(jobId);
    }    
  }

  loadJob();
}

jobRunNowModalController.$inject = ["$scope", "$uibModalInstance"];

/**
 * jobRunNowModalController - Controller for the reset interval popup.
 * @param  {Object} $scope             Angular's $scope object.
 * @param  {Object} $uibModalInstance  Object for the modal popup window.
 */
export function jobRunNowModalController($scope, $uibModalInstance) {
  $scope.setIntervalReset = function (result) {
    $uibModalInstance.close(result);
  };

  $scope.cancelRunNow = function () {
    $uibModalInstance.dismiss("cancel")
  };
}