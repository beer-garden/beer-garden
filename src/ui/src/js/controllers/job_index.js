import {formatDate} from '../services/utility_service.js';

jobIndexController.$inject = ['$scope', 'JobService'];

/**
 * jobIndexController - Controller for the job index page.
 * @param  {Object} $scope      Angular's $scope object.
 * @param  {Object} JobService  Beer-Garden's job service.
 */
export default function jobIndexController($scope, JobService) {
  $scope.setWindowTitle('scheduler');

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
