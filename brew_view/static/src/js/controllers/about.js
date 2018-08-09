
AboutController.$inject = ['$scope', 'UtilityService'];

/**
 * AboutController - Angular controller for the about page.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {Object} VersionService Beer-Garden's version service object.
 */
export default function AboutController($scope, UtilityService) {
  $scope.version = {
    data: {},
    loaded: false,
    error: false,
    errorMessage: '',
  };

  $scope.successCallback = function(response) {
    $scope.version.data = response.data;
    $scope.version.loaded = true;
    $scope.version.error = false;
    $scope.version.errorMessage = '';
  },

  $scope.failureCallback = function(response) {
    $scope.version.data = {};
    $scope.version.loaded = false;
    $scope.version.error = true;
    $scope.version.errorMessage = response.data.message;
  },

  UtilityService.getVersion().then(
    $scope.successCallback,
    $scope.failureCallback
  );
};
