import _ from "lodash";
import angular from "angular";

loginController.$inject = [
  "$scope",
  "$timeout",
  "$uibModalInstance",
  "TokenService",
];

/**
 * loginController - Login controller
 * @param  {Object} $scope                        Angular's $scope object.
 * @param  {Object} $timeout                        Angular's $timeout object.
 * @param  {Object} $uibModalInstance  Angular UI's $uibModalInstance object.
 * @param  {Object} TokenService  TokenService object.
 */
export default function loginController(
  $scope,
  $timeout,
  $uibModalInstance,
  TokenService
) {
  $scope.model = {};

  $scope.doLogin = function () {
    $scope.badUsername = false;
    $scope.badPassword = false;

    TokenService.doLogin($scope.model.username, $scope.model.password).then(
      (response) => {
        $uibModalInstance.close();
      },
      () => {
        if (_.isUndefined($scope.model.username)) {
          $scope.badUsername = true;
          angular.element('input[type="text"]').focus();
        } else {
          $scope.badPassword = true;
          $scope.model.password = undefined;
          angular.element('input[type="password"]').focus();
        }
      }
    );
  };

  $scope.cancel = function () {
    $uibModalInstance.dismiss();
  };

  $timeout(() => {
    angular.element('input[type="text"]').focus();
  });
}
