
systemIndexController.$inject = [
  '$scope',
  '$rootScope',
  '$state',
  '$stateParams',
  'SystemService',
  'UtilityService',
  'DTOptionsBuilder',
];

/**
 * systemIndexController - Controller for the system index page.
 * @param  {Object} $scope         Angular's $scope object.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {Object} $state         Angular's $state object.
 * @param  {Object} SystemService  Beer-Garden's sytem service.
 * @param  {Object} UtilityService Beer-Garden's utility service.
 */
export default function systemIndexController(
    $scope,
    $rootScope,
    $state,
    $stateParams,
    SystemService,
    UtilityService,
    DTOptionsBuilder
    ) {
  $scope.setWindowTitle();

  $scope.util = UtilityService;

  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('autoWidth', false)
    .withOption('order', [[0, 'asc'], [1, 'asc'], [2, 'asc'], [3, 'asc']])
    .withLightColumnFilter({
      0: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      1: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      2: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      3: {html: 'input', type: 'text', attr: {class: 'form-inline form-control'}},
      4: {html: 'input', type: 'number', attr: {class: 'form-inline form-control'}},
      5: {html: 'input', type: 'number', attr: {class: 'form-inline form-control'}},
    })
    .withBootstrap();

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  $scope.buildBreadCrumbs = function() {

    var dirDisplay =  [".."];

    if ('namespace' in $stateParams){
        dirDisplay.push($stateParams.namespace);

        if ('system' in $stateParams){
          dirDisplay.push($stateParams.system);
        }
    }

    if (dirDisplay.length == 1){
      var dirDisplay =  ["Systems"];
    }
    $scope.breadCrumbs = dirDisplay;

  }

  $scope.response = $rootScope.sysResponse;
  $scope.data = $rootScope.systems;
};
