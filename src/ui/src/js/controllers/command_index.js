commandIndexController.$inject = [
  '$rootScope',
  '$scope',
  'DTOptionsBuilder',
];

/**
 * commandIndexController - Angular controller for all commands page.
 * @param  {$rootScope} $rootScope   Angular's $rootScope object.
 * @param  {$scope} $scope           Angular's $scope object.
 * @param  {Object} DTOptionsBuilder Data-tables' builder for options.
 */
export default function commandIndexController(
    $rootScope,
    $scope,
    DTOptionsBuilder) {
  $scope.setWindowTitle('commands');
  $scope.filterHidden = false;
  $scope.dtInstance = {};
  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('order', [[0, 'asc'], [1, 'asc'], [2, 'asc'], [3, 'asc']])
    .withOption('autoWidth', false)
    .withOption('hiddenContainer', true)
    .withBootstrap();

  $scope.hiddenComparator = function(hidden, checkbox){
    return checkbox || !hidden;
  };

  $scope.nodeMove = function(location){
    var node = document.getElementById("filterHidden");
    var list = document.getElementById(location);
    list.append(node, list.childNodes[0]);
  };

  $scope.successCallback = function(response) {
    // Pull out what we care about
    let commands = [];

    response.data.forEach((system) => {
      system.commands.forEach((command) => {
        commands = commands.concat({
          hidden: command.hidden,
          id: command.id,
          namespace: system.namespace,
          name: command.name,
          system: system.display_name || system.name,
          version: system.version,
          description: command.description || 'No Description Provided',
        });
      });
    });

    $scope.response = response;
    $scope.data = commands;
    $scope.dtOptions.withLanguage({"info": "Showing _START_ to _END_ of _TOTAL_ entries (filtered from " +
    $scope.data.length + " total entries)", "infoFiltered":   ""});
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  $scope.successCallback($rootScope.sysResponse);
};
