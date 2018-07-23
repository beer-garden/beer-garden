
LoginController.$inject = [
  '$scope',
  '$rootScope',
  '$http',
  '$state',
  'localStorageService',
  'UserService',
  'TokenService',
];

/**
 * LoginController - Angular controller for the login page.
 * @param  {$scope} $scope                 Angular's $scope object.
 * @param  {$rootScope} $rootScope         Angular's $rootScope object.
 * @param  {$http} $http                   Angular's $http object.
 * @param  {$state} $state                 Angular's $state object.
 * @param  {localStorageService} localStorageService Storage service
 * @param  {UserService} UserService       Service for User information.
 * @param  {TokenService} TokenService     Service for Token information.
 */
export default function LoginController(
    $scope,
    $rootScope,
    $http,
    $state,
    localStorageService,
    UserService,
    TokenService) {
  $scope.doLogin = function(user) {
    TokenService.doLogin(user.username, user.password)
    .then(response => {
      TokenService.handleRefresh(response.data.refresh);
      TokenService.handleToken(response.data.token);

      $state.go('landing');
    }, response => {
      console.log(response.data);
    });
  };

  $scope.doCreate = function(user) {
    UserService.createUser(user.username, user.password);
  };
};
