systemIndexController.$inject = [
  '$scope',
  '$rootScope',
  'localStorageService',
  'UtilityService',
  'DTOptionsBuilder',
];

/**
 * systemIndexController - Controller for the system index page.
 * @param  {Object} $scope         Angular's $scope object.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {Object} localStorageService  Storage service
 * @param  {Object} UtilityService Beer-Garden's utility service.
 * @param  {Object} DTOptionsBuilder
 */
export default function systemIndexController(
    $scope,
    $rootScope,
    localStorageService,
    UtilityService,
    DTOptionsBuilder,
) {
  $scope.setWindowTitle();

  $scope.util = UtilityService;

  $scope.hasGroups = false;

  $scope.filters = {
    0: {
      html: 'input',
      type: 'text',
      attr: {class: 'form-inline form-control', title: 'Namespace Filter'},
    },
    1: {
      html: 'input',
      type: 'text',
      attr: {class: 'form-inline form-control', title: 'System Filter'},
    },
    2: {
      html: 'input',
      type: 'text',
      attr: {class: 'form-inline form-control', title: 'Version Filter'},
    },
    3: {
      html: 'input',
      type: 'text',
      attr: {
        class: 'form-inline form-control',
        title: 'Description Filter',
      },
    },
    4: {
      html: 'input',
      type: 'number',
      attr: {class: 'form-inline form-control', title: 'Commands Filter'},
    },
    5: {
      html: 'input',
      type: 'number',
      attr: {class: 'form-inline form-control', title: 'Instances Filter'},
    },
  };

  $scope.dtOptions = DTOptionsBuilder.newOptions()
      .withOption('autoWidth', false)
      .withOption(
          'pageLength',
          localStorageService.get('_system_index_length') || 10,
      )
      .withOption('order', [
        [0, 'asc'],
        [1, 'asc'],
        [2, 'asc'],
        [3, 'asc'],
      ])
      .withLightColumnFilter($scope.filters)
      .withBootstrap();

  $scope.instanceCreated = function(_instance) {
    $scope.dtInstance = _instance;

    $('#systemIndexTable').on('length.dt', (event, settings, len) => {
      localStorageService.set('_system_index_length', len);
    });
  };

  $scope.checkGroups = function() {
    $scope.hasGroups = false;
    for (let i = 0; i < $rootScope.systems.length; i++){
      if ($rootScope.systems[i].groups.length > 0){
        $scope.hasGroups = true;
        break;
      }
    }

    if ($scope.hasGroups && !(6 in $scope.filters)){
      $scope.filters[6] = {
        html: 'input',
        type: 'text',
        attr: {class: 'form-inline form-control', title: 'Group Filter', ng: 'Group Filter'},
      };
    } else if (!$scope.hasGroups && 6 in $scope.filters){
      delete  $scope.filters[6];
    }
  }

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data.filter($rootScope.isSystemRoutable);
    $scope.checkGroups();
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
    $scope.checkGroups();
  };

  $scope.response = $rootScope.gardensResponse;
  $scope.data = $rootScope.systems.filter($rootScope.isSystemRoutable);
  $scope.checkGroups();

}
