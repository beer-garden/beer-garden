gardenConfigExportController.$inject =
    ['$scope', '$rootScope', '$filter', 'GardenService'];

/**
 * gardenConfigExportController - Controller for the garden config export page.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $rootScope        Angular's $rootScope object.
 * @param  {Object} $filter           Filter
 * @param  {Object} GardenService     Beer-Garden's garden service.
 */
export default function gardenConfigExportController(
    $scope,
    $rootScope,
    $filter,
    GardenService,
) {
  $scope.response = $rootScope.sysResponse;

  $scope.exportGardenConfig = (gardenName) => {
    const filename =
      `GardenExport_${gardenName}_` +
      $filter('date')(new Date(Date.now()), 'yyyyMMdd_HHmmss');

    const formModel = GardenService.formToServerModel($scope.data, $scope.gardenModel);

    const [newConnectionInfo, newConnectionParams] = [{}, {}];
    newConnectionInfo['connection_type'] = formModel['connection_type'];

    if (formModel['connection_params']['http']) {
      newConnectionParams['http'] = formModel['connection_params']['http'];
    }

    if (formModel['connection_params']['stomp']) {
      newConnectionParams['stomp'] = formModel['connection_params']['stomp'];
    }

    newConnectionInfo['connection_params'] = newConnectionParams;

    const blob = new Blob(
        [JSON.stringify(newConnectionInfo)],
        {
          type: 'application/json;charset=utf-8',
        },
    );
    const downloadLink = angular.element('<a></a>');

    downloadLink.attr('href', window.URL.createObjectURL(blob));
    downloadLink.attr('download', filename);
    downloadLink[0].click();
  };
}
