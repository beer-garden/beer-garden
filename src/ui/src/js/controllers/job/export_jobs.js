jobExportController.$inject = ['$scope', '$rootScope', '$filter', 'JobService'];

/**
 * jobExportController - Controller for the job export page.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $rootScope        Angular's $rootScope object.
 * @param  {Object} $filter
 * @param  {Object} JobService        Beer-Garden's job service.
 */
export default function jobExportController(
    $scope,
    $rootScope,
    $filter,
    JobService,
) {
  $scope.response = $rootScope.sysResponse;
  $scope.data = $rootScope.systems;

  $scope.exportAllJobs = function() {
    JobService.exportJobs().then(
        function(response) {
          const filename = 'JobExport_' +
                            $filter('date')(new Date(Date.now()), 'yyyyMMdd_HHmmss');
          const blob = new Blob([JSON.stringify(response.data)], {
            type: 'application/json;charset=utf-8',
          });
          const downloadLink = angular.element('<a></a>');
          downloadLink.attr('href', window.URL.createObjectURL(blob));
          downloadLink.attr('download', filename);
          downloadLink[0].click();
        },
        () => alert('Aborting: No Jobs defined or unknown error.'),
    );
  };
}
