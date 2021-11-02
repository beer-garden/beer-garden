
jobExportSystemsController.$inject = [ '$scope', '$rootScope', 'JobService' ];

/**
 * jobExportSystemsController - Controller for the job export page.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $rootScope        Angular's $rootScope object.
 * @param  {Object} JobService        Beer-Garden's job service.
 */
export default function jobExportSystemsController( $scope, $rootScope, JobService) {
  $scope.setWindowTitle('Export');

  $scope.response = $rootScope.sysResponse;
  $scope.data = $rootScope.systems;

  function getFilename() {
    let currentDate = new Date(Date.now());
    let fmt = function (nbr) {
      return (nbr < 10 ? "0" : "") + nbr.toString()
    }
    let year = (currentDate.getUTCFullYear()).toString(),
      month = fmt(currentDate.getUTCMonth() + 1),
      day = fmt(currentDate.getUTCDate()),
      hour = fmt(currentDate.getUTCHours()),
      minutes = fmt(currentDate.getUTCMinutes()),
      seconds = fmt(currentDate.getUTCSeconds())
    
      return 'JobExport_' + year + month + day + "_"
        + hour + minutes + seconds
  };

  $scope.exportAllSystems = function() {
    JobService.exportJobs().then(
      function(response) {
        let filename = getFilename();
        let blob = new Blob([JSON.stringify(response.data)], {type: 'application/json;charset=utf-8'});
        let downloadLink = angular.element('<a></a>')
        downloadLink.attr('href', window.URL.createObjectURL(blob))
        downloadLink.attr('download', filename)
        downloadLink[0].click()
      },
      () => alert("Aborting: No Jobs defined or unknown error.")
    )
  }
};
