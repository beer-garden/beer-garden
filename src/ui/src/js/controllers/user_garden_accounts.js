userGardenAccountsController.$inject = ['$scope', '$rootScope', '$uibModalInstance', '$sce', 'UserService', 'GardenService', 'user'];

/**
 * userGardenAccountsController - Controller for change user accounts modal.
 * @param  {Object} $scope             Angular's $scope object.
 * @param  {Object} $rootScope     Angular's $rootScope object.
 * @param  {$scope} $uibModalInstance  Angular UI's $uibModalInstance object.
 * @param  {Object} $sce             Angular's $sce object.
 * @param  {Object} UserService        Beer-Garden's user service.
 * @param  {Object} GardenService      Beer-Garden's garden service.
 * @param  {Object} User               User model to modify
 */
export default function userGardenAccountsController($scope, $rootScope, $uibModalInstance, $sce, UserService, GardenService, user) {
    $scope.close = function() {
        $uibModalInstance.close();
      };
    
    $scope.user = user;

    $scope.addGardenNames = function(garden = null) {
      if (garden == null){
        garden = $rootScope.garden;
      } else {
        if ($scope.editUser.remote_user_mapping.length == 0){
          $scope.editUser.remote_user_mapping.push({"target_garden":garden.name, "username":null})
        } else {
          let foundMapping = false;

          for (const user_mapping of $scope.editUser.remote_user_mapping){
            if (garden.name == user_mapping.target_garden){
              foundMapping = true;
              break;
            }
          }

          if (!foundMapping){
            $scope.editUser.remote_user_mapping.push({"target_garden":garden.name, "username":null})
          }
        }
       
      }

      if (garden.children !== undefined && garden.children != null && garden.children.length > 0){
        for (const childGarden of garden.children){
          $scope.addGardenNames(childGarden);
        }
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

    $scope.findParentGardenRoute = function(gardenName) {
      return $sce.trustAsHtml($scope.findParentGardenRouteHtml(gardenName))
    }

    $scope.findParentGardenRouteHtml = function (gardenName, route = null) {
      if (route == null){
        route = gardenName;
      }

      let parent = $scope.findParentGarden(gardenName);

      if (parent == null){
        return route;
      } else {
        route = "<span> " + parent + ' </span><span class="fa fa-arrow-right" ></span><span> ' + route + " </span>";      
        return $scope.findParentGardenRouteHtml(parent, route);
      }
    }

    $scope.findDefaultUsername = function(gardenName) {
      let parentGarden = $scope.findParentGarden(gardenName);
      if (parentGarden == null) {
        return $scope.editUser.username;
      }

      for (const user_mapping of $scope.editUser.remote_user_mapping){
        if (parentGarden == user_mapping.target_garden){
          if (user_mapping.username !== undefined && user_mapping.username != null){
            return user_mapping.username;
          }
          break;
        }
      }

      return $scope.findDefaultUsername(parentGarden);
    }

    $scope.submitAccounts = function() {
      let populatedAccounts = [];
      for (const user_mapping of $scope.editUser.remote_user_mapping){
        if (user_mapping.username !== undefined && user_mapping.username != null && user_mapping.username.length > 0){
          populatedAccounts.push(user_mapping);
        }
      }
      $scope.user.remote_user_mapping = populatedAccounts;
      UserService.updateUserAccounts($scope.user.username, $scope.user);
    }
   

}