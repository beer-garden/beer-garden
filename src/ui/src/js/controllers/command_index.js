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
  $scope.filterHidden = false;
  $scope.dtInstance = {};
  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('autoWidth', false)
    .withOption('hiddenContainer', true)
    .withOption('order', [[0, 'asc'], [1, 'asc'], [2, 'asc'], [3, 'asc']])
    .withBootstrap();

  $scope.hiddenComparator = function(hidden, checkbox){
    return checkbox || !hidden;
  };

  $scope.nodeMove = function(location){
    var node = document.getElementById("filterHidden");
    var list = document.getElementById(location);
    list.append(node, list.childNodes[0]);
  };
  
  if (!($stateParams.namespace || $stateParams.systemName || $stateParams.systemVersion)) {
    $scope.dtOptions = $scope.dtOptions.withLightColumnFilter({
      0: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      1: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      2: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      3: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      4: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
    })
  }

  $scope.successCallback = function(response) {
    // Pull out what we care about
    let commands = [];
    let breadCrumbs = [];

    response.data.forEach((system) => {
      system.commands.forEach((command) => 
        commands.push({
          id: command.id,
          hidden: command.hidden,
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
    $scope.dtOptions.withLanguage({"info": "Showing _START_ to _END_ of _TOTAL_ entries (filtered from " +
    $scope.data.length + " total entries)", "infoFiltered":   ""});
    $scope.breadCrumbs = breadCrumbs;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  $scope.successCallback($rootScope.sysResponse);
};
