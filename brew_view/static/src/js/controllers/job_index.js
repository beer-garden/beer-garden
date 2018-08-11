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
  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  $scope.formatDate = formatDate;

  function loadJobs() {
    $scope.response = undefined;
    $scope.data = {};

    JobService.getJobs().then(
      $scope.successCallback,
      $scope.failureCallback
    );
  }

  $scope.$on('userChange', () => {
    loadJobs();
  });

  loadJobs();
};
