
AboutController.$inject = ['$scope', 'UtilityService'];

/**
 * AboutController - Angular controller for the about page.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {Object} VersionService Beer-Garden's version service object.
 */
export default function AboutController($scope, UtilityService) {
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
