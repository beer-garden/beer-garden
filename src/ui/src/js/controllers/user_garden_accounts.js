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
        if ($scope.editUser.user_alias_mapping.length == 0){
          $scope.editUser.user_alias_mapping.push({"target_garden":garden.name, "username":null})
        } else {
          let foundMapping = false;

          for (const user_mapping of $scope.editUser.user_alias_mapping){
            if (garden.name == user_mapping.target_garden){
              foundMapping = true;
              break;
            }
          }

          if (!foundMapping){
            $scope.editUser.user_alias_mapping.push({"target_garden":garden.name, "username":null})
          }
        }
       
      }

      if (garden.downstream !== undefined && garden.downstream != null && garden.downstream.length > 0){
        for (const downstreamGarden of garden.downstream){
          $scope.addGardenNames(downstreamGarden);
        }
      }
    }

    $scope.resetSubmission = function() {
      $scope.editUser = angular.copy($scope.user);
      $scope.addGardenNames()
    }

    $scope.resetSubmission();

    $scope.findUpstreamGarden = function (gardenName, garden = null) {
      if (garden == null){
        garden = $rootScope.garden;
      }

      // Loop through downstream to determine if upstream is the garden
      if (garden.downstream !== undefined && garden.downstream != null && garden.downstream.length > 0){
        for (let i = 0; i < garden.downstream.length; i++) {
          if (garden.downstream[i].name == gardenName){
            return garden.name;
          }
          let upstreamName = $scope.findUpstreamGarden(gardenName, garden.downstream[i]);
          if (upstreamName != null){
            return upstreamName;
          }    
        }
      }
      return null;
    }

    $scope.findGardenDefaultUsername = function (gardenName, garden = null) {
      if (garden == null){
        garden = $rootScope.garden;
      }

      if (garden.name == gardenName){
        if (garden.default_user !== undefined && garden.default_user != null){
          return garden.default_user;
        }
      }

      if (garden.downstream !== undefined && garden.downstream != null && garden.downstream.length > 0){
        for (let i = 0; i < garden.downstream.length; i++) {
          let childDefaultUser = $scope.findGardenDefaultUsername(gardenName, garden.downstream[i]);
          if (childDefaultUser != null){
            return childDefaultUser;
          }   
        }
      }

      return null;
    }

    $scope.findUpstreamGardenRoute = function(gardenName) {
      return $sce.trustAsHtml($scope.findUpstreamGardenRouteHtml(gardenName))
    }

    $scope.findUpstreamGardenRouteHtml = function (gardenName, route = null) {
      if (route == null){
        route = gardenName;
      }

      let upstream = $scope.findUpstreamGarden(gardenName);

      if (upstream == null){
        return route;
      } else {
        route = "<span> " + upstream + ' </span><span class="fa fa-arrow-right" ></span><span> ' + route + " </span>";      
        return $scope.findUpstreamGardenRouteHtml(upstream, route);
      }
    }

    $scope.findDefaultUsername = function(gardenName) {

      let gardenDefaultUsername = $scope.findGardenDefaultUsername(gardenName);
      if (gardenDefaultUsername != null){
        return gardenDefaultUsername;
      }
      
      let upstreamGarden = $scope.findUpstreamGarden(gardenName);
      if (upstreamGarden == null) {
        return $scope.editUser.username;
      }

      for (const user_mapping of $scope.editUser.user_alias_mapping){
        if (upstreamGarden == user_mapping.target_garden){
          if (user_mapping.username !== undefined && user_mapping.username != null){
            return user_mapping.username;
          }
          break;
        }
      }

      return $scope.findDefaultUsername(upstreamGarden);
    }

    $scope.submitAccounts = function() {
      let populatedAccounts = [];
      for (const user_mapping of $scope.editUser.user_alias_mapping){
        if (user_mapping.username !== undefined && user_mapping.username != null && user_mapping.username.length > 0){
          populatedAccounts.push(user_mapping);
        }
      }
      $scope.user.user_alias_mapping = populatedAccounts;
      UserService.updateUserAccounts($scope.user.username, $scope.user);
    }
   

}