import jwtDecode from 'jwt-decode';

LoginController.$inject = ['$scope', '$rootScope', '$http', '$state',
  'localStorageService', 'UserService'];

/**
 * LoginController - Angular controller for the login page.
 */
export default function LoginController($scope, $rootScope, $http, $state,
    localStorageService, userService) {

  $scope.doLogin = function(model) {
    $http.post('login', {username: model.username, password: model.password})
    .then(function(response) {
      let token = response.data.token;

      // Save the token to session storage in case we need it later
      localStorageService.set('token', token);

      // Use the token for all subsequent requests
      $http.defaults.headers.common.Authorization = 'Bearer ' + token;

      // Now grab the user id and roles from the token
      let decoded = jwtDecode(token);
      let userId = decoded.sub;

      // Finally, grab the user definition from the API
      $http.get('api/v1/users/' + userId).then(function(response) {
        $rootScope.user = response.data;
        $rootScope.changeTheme($rootScope.user.preferences.theme || 'default');
      });

      $state.go('landing');
    });
  };

  $scope.doCreate = function(user) {
    userService.createUser(user.username, user.password);
  };
};
