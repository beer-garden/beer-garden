jobViewController.$inject = [
  '$scope',
  '$rootScope',
  '$location',
  '$stateParams',
  'UtilityService',
  'JobService',
];

/**
 * jobViewController - Controller for the job view page.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {$rootScope} $rootScope Angular's $rootScope object.
 * @param  {$location} $location   Angular's $location object.
 * @param  {$stateParams} $stateParams Angular's $stateParams object.
 * @param  {Object} UtilityService Beer-Garden's utility service.
 * @param  {Object} JobService Beer-Garden's job service.
 */
export default function jobViewController(
  $scope,
  $rootScope,
  $location,
  $stateParams,
  UtilityService,
  JobService) {
  $scope.job = {
    data: [],
    loaded: false,
    error: false,
    errorMessage: '',
    status: null,
    errorMap: {
    },
  };

  $scope.formattedRequestTemplate = '';
  $scope.formattedTrigger = '';

  $scope.loadPreview = function(_editor) {
      UtilityService.formatJsonDisplay(_editor, true);
  };

  $scope.formatDate = function(data) {
      return UtilityService.formatDate(data);
  };

  $scope.successCallback = function(response) {
    $scope.job.data = response.data;
    $scope.job.loaded = true;
    $scope.job.error = false;
    $scope.job.status = response.status;
    $scope.job.errorMessage = '';

    $scope.formattedRequestTemplate = JSON.stringify(
        $scope.job.data.request_template,
        undefined,
        2
    );
    $scope.formattedTrigger = JSON.stringify(
        $scope.job.data.trigger,
        undefined,
        2
    );
  };

  $scope.resumeJob = function(jobId) {
      JobService.resumeJob(jobId)
        .then(
            $scope.successCallback,
            $scope.failureCallback
        );
  };

  $scope.pauseJob = function(jobId) {
      JobService.pauseJob(jobId)
        .then(
            $scope.successCallback,
            $scope.failureCallback
        );
  };

  $scope.deleteJob = function(jobId) {
      JobService.deleteJob(jobId)
        .then(
            $location.path('/jobs'),
            function(response) {
                $scope.job.error = true;
                $scope.job.errorMessage = response.data.message;
            }
        );
  };

  $scope.failureCallback = function(response) {
    $scope.job.data = [];
    $scope.job.loaded = false;
    $scope.job.error = true;
    $scope.job.status = response.status;
    $scope.job.errorMessage = response.data.message;
  };

  JobService.getJob($stateParams.id).then($scope.successCallback, $scope.failureCallback);
};
