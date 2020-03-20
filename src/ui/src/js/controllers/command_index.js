
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

  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('order', [[0, 'asc'], [1, 'asc'], [2, 'asc'], [3, 'asc']])
    .withOption('autoWidth', false)
    .withBootstrap();

  $scope.successCallback = function(response) {
    // Pull out what we care about
    let commands = [];

    response.data.forEach((system) => {
      system.commands.forEach((command) => {
        commands = commands.concat({
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
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  $scope.successCallback($rootScope.sysResponse);
};
