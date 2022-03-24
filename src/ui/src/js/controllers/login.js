import angular from 'angular';

loginController.$inject = [
  '$scope',
  '$timeout',
  '$uibModalInstance',
  'TokenService',
];

/**
 * loginController - Login controller
 * @param  {Object} $scope             Angular's $scope object.
 * @param  {Object} $timeout           Angular's $timeout object.
 * @param  {Object} $uibModalInstance  Angular UI's $uibModalInstance object.
 * @param  {Object} TokenService       TokenService object.
 */
export default function loginController(
    $scope,
    $timeout,
    $uibModalInstance,
    TokenService,
) {
  $scope.model = {};

  $scope.doLogin = function() {
    $scope.loginFailed = false;

    TokenService.doLogin($scope.model.username, $scope.model.password).then(
        loginSuccess,
        loginFailure,
    );
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss();
  };

  const loginSuccess = function() {
    $uibModalInstance.close();
  };

  const loginFailure = function() {
    $scope.loginFailed = true;
    angular.element('input[id="password"]').focus();
  };

  $timeout(() => {
    angular.element('input[id="username"]').focus();
  });
}
