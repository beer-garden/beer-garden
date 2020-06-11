
commandIndexController.$inject = [
  '$rootScope',
  '$scope',
  '$stateParams',
  'DTOptionsBuilder',
  'DTColumnBuilder',
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
    $stateParams,
    DTOptionsBuilder) {
  $scope.setWindowTitle('commands');

  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('autoWidth', false)
    .withOption('order', [[0, 'asc'], [1, 'asc'], [2, 'asc'], [3, 'asc']])
    .withBootstrap();

  if (!($stateParams.namespace || $stateParams.systemName || $stateParams.systemVersion)) {
    $scope.dtOptions = $scope.dtOptions.withLightColumnFilter({
      0: {html: 'input', type: 'text', attr: {class: 'form-inline form-control', title: 'Namespace Filter'}},
      1: {html: 'input', type: 'text', attr: {class: 'form-inline form-control', title: 'System Filter'}},
      2: {html: 'input', type: 'text', attr: {class: 'form-inline form-control', title: 'Version Filter'}},
      3: {html: 'input', type: 'text', attr: {class: 'form-inline form-control', title: 'Command Filter'}},
      4: {html: 'input', type: 'text', attr: {class: 'form-inline form-control', title: 'Description Filter'}},
    })
  }

  $scope.successCallback = function(response) {
    // Pull out what we care about
    let commands = [];
    let breadCrumbs = [];

    response.data.forEach((system) => {
      system.commands.forEach((command) => {
        commands.push({
          id: command.id,
          namespace: system.namespace,
          name: command.name,
          system: system.display_name || system.name,
          version: system.version,
          description: command.description || 'No Description Provided',
        });
      });
    });

    if ($stateParams.namespace){
      commands = _.filter(commands, {namespace: $stateParams.namespace});
      breadCrumbs.push($stateParams.namespace);

      if ($stateParams.systemName){
        commands = _.filter(commands, {system: $stateParams.systemName});
        breadCrumbs.push($stateParams.systemName);

        if ($stateParams.systemVersion){
          commands = _.filter(commands, {version: $stateParams.systemVersion});
          breadCrumbs.push($stateParams.systemVersion);
        }
      }
    }

    $scope.response = response;
    $scope.data = commands;
    $scope.breadCrumbs = breadCrumbs;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  $scope.successCallback($rootScope.sysResponse);
};
