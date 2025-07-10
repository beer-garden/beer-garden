import {formatDate} from '../services/utility_service.js';

jobIndexController.$inject = ['$scope', '$rootScope', 'JobService','EventService'];

/**
 * jobIndexController - Controller for the job index page.
 * @param  {Object} $scope      Angular's $scope object.
 * @param  {Object} $rootScope      Angular's $rootScope object.
 * @param  {Object} JobService  Beer-Garden's job service.
 * @param  {Object} EventService    Beer-Garden's event service object.
 */
export default function jobIndexController($scope, $rootScope, JobService, EventService) {
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
    JobService.getJobs().then($scope.successCallback, $scope.failureCallback);
  }

  function eventCallback(event) {
    if ($rootScope.garden !== undefined && event.garden == $rootScope.garden.name) {
      if (['JOB_PAUSED', 'JOB_RESUMED', 'JOB_COUNTER_UPDATED'].includes(event.name)) {
        for (let job in $scope.data){
          if ($scope.data[job].id == event.payload.id){
            $scope.data[job] = event.payload
          }
        }
      } else if (event.name.startsWith('JOB')) {
        loadJobs();
      }
    }
  }

  EventService.addCallback('job_index', (event) => {
    $scope.$apply(() => {
      eventCallback(event);
    });
  });

  $scope.$on('$destroy', function() {
    EventService.removeCallback('job_index');
  });

  $scope.$on('userChange', () => {
    loadJobs();
  });

  loadJobs();
}
