
AboutController.$inject = ['$scope', 'VersionService'];

/**
 * AboutController - Angular controller for the about page.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {Object} VersionService Beer-Garden's version service object.
 */
export default function AboutController($scope, VersionService) {
  $scope.version = {
    data: {},
    loaded: false,
    error: false,
    errorMessage: '',
    errorMap: {
      'empty': {
        'solutions': [
          {
            problem: 'Could not get version information',
            description: 'The web service is down. Odd that you can still get to this page, ' +
                         'right? You should probably restart the service. If other pages are ' +
                         'still running after a hard refresh (ctrl-F5) then you should contact ' +
                         'a developer.',
            resolution: '<kbd>service brew-view restart</kbd>',
          },
        ],
      },
    },
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

  VersionService.getVersionInfo()
    .then($scope.successCallback, $scope.failureCallback);
};
