
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
    .withLightColumnFilter({
      0: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      1: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      2: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      3: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      4: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
    })
    .withBootstrap();


  $scope.successCallback = function(response) {
    // Pull out what we care about
    let commands = [];

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

    $scope.response = response;
    $scope.data = commands;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  $scope.successCallback($rootScope.sysResponse);

  $scope.buildBreadCrumbs = function() {

    var dirDisplay =  [".."];

    if ('namespace' in $stateParams){
        dirDisplay.push($stateParams.namespace);

        if ('systemName' in $stateParams){
          dirDisplay.push($stateParams.systemName);

          if ('systemVersion' in $stateParams){
            dirDisplay.push($stateParams.systemVersion);
          }
        }
    }

    if (dirDisplay.length == 1){
      var dirDisplay =  ["Available Commands"];
    }
    $scope.breadCrumbs = dirDisplay;

  }

  $scope.getPageFilter = function (command) {

    if ('namespace' in $stateParams){
        if (command.namespace != $stateParams.namespace){
          return false;
        }
     }
     else if ('systemName' in $stateParams){
        if (command.system != $stateParams.systemName){
          return false
        }
     }
     else if ('systemVersion' in $stateParams){
        if (command.version != $stateParams.systemVersion){
          return false
        }
     }

    return true;
  }
};
