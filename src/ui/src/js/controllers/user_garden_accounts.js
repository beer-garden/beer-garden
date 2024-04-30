addRemoveRolesController.$inject = ['$scope', '$rootScope', '$uibModalInstance', 'UserService', 'GardenService', 'user'];

/**
 * addRemoveRolesController - Controller for change user roles modal.
 * @param  {Object} $scope             Angular's $scope object.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {$scope} $uibModalInstance  Angular UI's $uibModalInstance object.
 * @param  {Object} UserService        Beer-Garden's user service.
 * @param  {Object} GardenService      Beer-Garden's garden service.
 * @param  {Object} User               User model to modify
 */
export default function userGardenAccountsController($scope, $rootScope, $uibModalInstance, UserService, GardenService, user) {
    $scope.close = function() {
        $uibModalInstance.close();
      };
    
    $scope.user = user;

    $scope.addGardenNames = function(garden = null) {
      if (garden == null){
        garden = $rootScope.garden;
      }

      if ($scope.editUser.remote_user_mapping[garden.name] === undefined){
        $scope.editUser.remote_user_mapping[garden.name] = null;
      }
      if (garden.children !== undefined && garden.children != null && garden.children.length > 0){
        garden.children.array.forEach(childGarden => {
          $scope.addGardenNames(childGarden);
        });
      }
    }

    $scope.resetSubmission = function() {
      $scope.editUser = angular.copy($scope.user);
      $scope.addGardenNames()
    }

    $scope.resetSubmission();

    $scope.findParentGarden = function (gardenName, garden = null) {
      if (garden == null){
        garden = $rootScope.garden;
      }

      // Loop through children to determien if parent is the garden
      if (garden.children !== undefined && garden.children != null && garden.children.length > 0){
        for (let i = 0; i < garden.children.length; i++) {
          if (garden.children[i].name == gardenName){
            return garden.name;
          }
          let parentName = $scope.findParentGarden(gardenName, garden.children[i]);
          if (parentName != null){
            return parentName;
          }    
        }
      }
      return null;
    }

    $scope.findDefaultUsername = function(gardenName) {
      let parentGarden = $scope.findParentGarden(gardenName);
      if (parentGarden == null) {
        return null;
      }

      if ($scope.editUser.remote_user_mapping[parentGarden] !== undefined && $scope.editUser.remote_user_mapping[parentGarden] != null){
        return $scope.editUser.remote_user_mapping[parentGarden];
      }

      return $scope.findDefaultUsername(parentGarden);
    }

    $scope.submitAccounts = function() {
        UserService.updateUserAccounts($scope.editUser.username, $scope.editUser);
    }
   

}