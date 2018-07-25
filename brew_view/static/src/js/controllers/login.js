
LoginController.$inject = [
  '$scope',
  '$rootScope',
  '$state',
  'UserService',
  'TokenService',
];

/**
 * LoginController - Angular controller for the login page.
 * @param  {$scope} $scope                 Angular's $scope object.
 * @param  {$rootScope} $rootScope         Angular's $rootScope object.
 * @param  {$state} $state                 Angular's $state object.
 * @param  {UserService} UserService       Service for User information.
 * @param  {TokenService} TokenService     Service for Token information.
 */
export default function LoginController(
    $scope,
    $rootScope,
    $state,
    UserService,
    TokenService) {
  $scope.doLogin = function(user) {
    TokenService.doLogin(user.username, user.password).then(
      (response) => {
        TokenService.handleRefresh(response.data.refresh);
        TokenService.handleToken(response.data.token);

        UserService.loadUser(response.data.token).then(
          (response) => {
            $rootScope.user = response.data;
            $rootScope.changeTheme($rootScope.user.preferences.theme || 'default');

            $state.go('landing');
          }, (response) => {
            console.log('error loading user');
          }
        );
      }, (response) => {
        console.log('bad login');
      }
    );
  };

  $scope.doCreate = function(user) {
    UserService.createUser(user.username, user.password);
  };
};
