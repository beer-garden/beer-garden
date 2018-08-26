import angular from 'angular';

loginController.$inject = [
  '$scope',
  '$rootScope',
  '$timeout',
  '$uibModalInstance',
  'TokenService',
];

/**
 * loginController - Login controller
 * @param  {Object} $scope                        Angular's $scope object.
 * @param  {Object} $rootScope                        Angular's $rootScope object.
 * @param  {Object} $timeout                        Angular's $timeout object.
 * @param  {Object} $uibModalInstance  Angular UI's $uibModalInstance object.
 * @param  {Object} TokenService  TokenService object.
 */
export default function loginController(
  $scope,
  $rootScope,
  $timeout,
  $uibModalInstance,
  TokenService,
) {
  $scope.doLogin = function() {
    TokenService.doLogin(
        $scope.model.username,
        $scope.model.password).then(
      (response) => {
        // $rootScope.loginInfo = {};
        // $rootScope.showLogin = false;
        $scope.badPassword = false;

        TokenService.handleRefresh(response.data.refresh);
        TokenService.handleToken(response.data.token);

        $rootScope.changeUser(response.data.token).then(
          () => {
            $rootScope.$broadcast('userChange');
          }
        );

        $uibModalInstance.close();
      }, (response) => {
        $scope.badPassword = true;
        $scope.model.password = undefined;
        angular.element('input[type="password"]').focus();
      }
    );
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss();
  };

  $timeout(() => {
    angular.element('input[type="text"]').focus();
  });
};
