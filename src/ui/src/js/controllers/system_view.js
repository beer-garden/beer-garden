import _ from 'lodash';

systemViewController.$inject = [
  '$scope',
  'UtilityService',
  'DTOptionsBuilder',
  'system',
];

/**
 * systemViewController - Angular Controller for viewing a single system.
 * @param  {$scope} $scope             Angular's $scope object.
 * @param  {Object} UtilityService     Beer-Garden Utility Service.
 * @param  {Object} DTOptionsBuilder   Object for building Data-Tables objects.
 */
export default function systemViewController(
    $scope,
    UtilityService,
    DTOptionsBuilder,
    system) {



  $scope.util = UtilityService;
  $scope.filterHidden = false;
  $scope.tableS;
  $scope.dtInstance = {};
  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('order', [4, 'asc'])
    .withOption('autoWidth', false)
    .withBootstrap();
  $scope.hiddenComparator = function(expected, actual){
    return actual || !expected;
  };


  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;
    $scope.setWindowTitle(
      ($scope.data.display_name || $scope.data.name),
      $scope.data.version
    );
    $scope.dtOptions.withLanguage({"info": "Showing _START_ to _END_ of _TOTAL_ entries (filtered from " +
        $scope.data.commands.length + " total entries)", "infoFiltered":   ""});
  };

  $scope.reloadData = function() {
     tb = $scope.dtInstance;
     $scope.dtInstance._renderer.rerender();
  }
  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
    $scope.setWindowTitle();
  };

  $scope.successCallback(system);
};
