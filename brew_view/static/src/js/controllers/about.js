
AboutController.$inject = ['$scope', 'UtilityService'];

/**
 * AboutController - Angular controller for the about page.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {Object} UtilityService Beer-Garden's utility service object.
 */
export default function AboutController($scope, UtilityService) {
  $scope.setWindowTitle('about');

  UtilityService.getVersion().then(
    (response) => {
      $scope.response = response;
      $scope.data = response.data;
    },
    (response) => {
      $scope.response = response;
    }
  );
};
