import {formatDate, formatJsonDisplay} from '../services/utility_service.js';

jobViewController.$inject = [
  '$scope',
  '$rootScope',
  '$location',
  '$stateParams',
  'JobService',
];

/**
 * jobViewController - Controller for the job view page.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {$rootScope} $rootScope Angular's $rootScope object.
 * @param  {$location} $location   Angular's $location object.
 * @param  {$stateParams} $stateParams Angular's $stateParams object.
 * @param  {Object} JobService Beer-Garden's job service.
 */
export default function jobViewController(
    $scope,
    $rootScope,
    $location,
    $stateParams,
    JobService) {
  $scope.formattedRequestTemplate = '';
  $scope.formattedTrigger = '';

  $scope.loadPreview = function(_editor) {
    formatJsonDisplay(_editor, true);
  };

  $scope.formatDate = function(data) {
    formatDate(data);
  };

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;

    $scope.formattedRequestTemplate = JSON.stringify(
      $scope.data.request_template,
      undefined,
      2
    );
    $scope.formattedTrigger = JSON.stringify(
      $scope.data.trigger,
      undefined,
      2
    );
  };

  $scope.resumeJob = function(jobId) {
    JobService.resumeJob(jobId).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  };

  $scope.pauseJob = function(jobId) {
    JobService.pauseJob(jobId).then(
      $scope.successCallback,
      $scope.failureCallback
    );
  };

  $scope.deleteJob = function(jobId) {
    JobService.deleteJob(jobId).then(
      $location.path('/jobs'),
      $scope.failureCallback
    );
  };

  $scope.failureCallback = function(response) {
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

  $scope.$on('userChange', () => {
    loadJob();
  });

  loadJob();
};
