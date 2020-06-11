
systemIndexController.$inject = [
  '$scope',
  '$rootScope',
  'UtilityService',
  'DTOptionsBuilder',
];

/**
 * systemIndexController - Controller for the system index page.
 * @param  {Object} $scope         Angular's $scope object.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {Object} UtilityService Beer-Garden's utility service.
 */
export default function systemIndexController(
    $scope,
    $rootScope,
    UtilityService,
    DTOptionsBuilder
    ) {
  $scope.setWindowTitle();

  $scope.util = UtilityService;

  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('autoWidth', false)
    .withOption('order', [[0, 'asc'], [1, 'asc'], [2, 'asc'], [3, 'asc']])
    .withLightColumnFilter({
      0: {html: 'input', type: 'text', attr: {class: 'form-inline form-control', title: 'Namespace Filter'}},
      1: {html: 'input', type: 'text', attr: {class: 'form-inline form-control', title: 'System Filter'}},
      2: {html: 'input', type: 'text', attr: {class: 'form-inline form-control', title: 'Version Filter'}},
      3: {html: 'input', type: 'text', attr: {class: 'form-inline form-control', title: 'Description Filter'}},
      4: {html: 'input', type: 'number', attr: {class: 'form-inline form-control', title: 'Commands Filter'}},
      5: {html: 'input', type: 'number', attr: {class: 'form-inline form-control', title: 'Instances Filter'}},
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

  $scope.response = $rootScope.sysResponse;
  $scope.data = $rootScope.systems;
};
