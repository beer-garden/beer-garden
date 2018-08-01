import {formatDate} from '../services/utility_service.js';

jobIndexController.$inject = [
  '$scope',
  '$rootScope',
  '$location',
  '$interval',
  'JobService',
];

/**
 * jobIndexController - Controller for the job index page.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {$rootScope} $rootScope Angular's $rootScope object.
 * @param  {$location} $location   Angular's $location object.
 * @param  {$interval} $interval   Angular's $interval object.
 * @param  {Object} JobService Beer-Garden's job service.
 */
export default function jobIndexController(
    $scope,
    $rootScope,
    $location,
    $interval,
    JobService,) {

  $scope.jobs = {
    data: [],
    loaded: false,
    error: false,
    errorMessage: '',
    status: null,
    errorMap: {
    },
  };

  $scope.successCallback = function(response) {
    $scope.jobs.data = response.data;
    $scope.jobs.loaded = true;
    $scope.jobs.error = false;
    $scope.jobs.status = response.status;
    $scope.jobs.errorMessage = '';
  };

  $scope.failureCallback = function(response) {
    $scope.jobs.data = [];
    $scope.jobs.loaded = false;
    $scope.jobs.error = true;
    $scope.jobs.status = response.status;
    $scope.jobs.errorMessage = response.data.message;
  };

  $scope.formatDate = formatDate;

  function loadJobs() {
    JobService.getJobs()
      .then($scope.successCallback, $scope.failureCallback);
  }

  $scope.$on('userChange', () => {
    loadJobs();
  });

  loadJobs();
};
