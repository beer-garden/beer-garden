addRemoveRolesController.$inject = ['$scope', '$uibModalInstance', 'UserService', 'GardenService', 'user'];

/**
 * addRemoveRolesController - Controller for change user roles modal.
 * @param  {Object} $scope             Angular's $scope object.
 * @param  {$scope} $uibModalInstance  Angular UI's $uibModalInstance object.
 * @param  {Object} UserService        Beer-Garden's user service.
 * @param  {Object} GardenService      Beer-Garden's garden service.
 * @param  {Object} User               User model to modify
 */
export default function userGardenAccountsController($scope, $uibModalInstance, UserService, GardenService, user) {
    $scope.close = function() {
        $uibModalInstance.close();
      };
    
    $scope.editUser = angular.copy(user);
    $scope.user = user;

    $scope.gardens = [];

    $scope.resetSubmission = function() {
      $scope.editUser = angular.copy($scope.user);
    }

    $scope.localRolesContains = function (role) {
        return $scope.user_roles.includes(role);
    }

    // $scope.findParentGarden = function (gardenName) {
    //   for
    //   return "";
    // }

    $scope.findParentGarden = function (gardenName, gardens) {
      // Loop through children to determien if parent is the garden
      for (let i = 0; i < gardens.length; i++) {
        if (gardens[i].children !== undefined && gardens[i].children != null && gardens[i].children.length > 0){
          
        }
      }
      return null;
    }

    $scope.submitAccounts = function() {
        UserService.updateUserAccounts($scope.editUser.username, $scope.editUser);
    }
   

}