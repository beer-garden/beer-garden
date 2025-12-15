addRemoveRolesController.$inject = ['$scope', '$uibModalInstance', 'UserService', 'RoleService', 'user'];

/**
 * addRemoveRolesController - Controller for change user roles modal.
 * @param  {Object} $scope             Angular's $scope object.
 * @param  {$scope} $uibModalInstance  Angular UI's $uibModalInstance object.
 * @param  {Object} UserService        Beer-Garden's user service.
 * @param  {Object} RoleService        Beer-Garden's role service.
 * @param  {Object} User               User model to modify
 */
export default function addRemoveRolesController($scope, $uibModalInstance, UserService, RoleService, user) {
    $scope.close = function() {
        $uibModalInstance.close();
      };
    
    $scope.user = user;
    // $scope.user.local_roles = [];
    $scope.user_roles = [...user.roles];
    $scope.data = [];

    $scope.resetSubmission = function() {
        $scope.user_roles = [];
        if ($scope.user.local_roles !== undefined && $scope.user.local_roles !== null) {
          for (let i = 0; i < $scope.user.local_roles.length; i++) {
              $scope.user_roles.push($scope.user.local_roles[i].name)
          }
        }

        if ($scope.data !== undefined && $scope.data !== null) {
          for (let i = 0; i < $scope.data.length; i++) {
              $scope.data[i].is_checked = $scope.user.roles.includes($scope.data[i].name)
          }
        }
    }

    $scope.localRolesContains = function (role) {
        return $scope.user_roles.includes(role);
    }

    $scope.onRoleCheckChange = function (role) {
        if (!$scope.user_roles.includes(role.name) && !role.is_checked){
            $scope.user_roles.push(role.name);
        } else  if ($scope.user_roles.includes(role.name) && role.is_checked){
            $scope.user_roles.splice($scope.user_roles.indexOf(role.name), 1);
        }
    }

    $scope.submitRoles = function() {
        $scope.user.roles = $scope.user_roles;

        UserService.updateUserRoles($scope.user.username, $scope.user).then($scope.close);
    }

    $scope.data = RoleService.getRoles().then(
        (responses) => {
            $scope.data = responses.data;
            if ($scope.data !== undefined && $scope.data !== null) {
              for (let i = 0; i < $scope.data.length; i++) {
                  $scope.data[i].is_checked = $scope.user.roles.includes($scope.data[i].name)
              }
            }
        },
        (response) => {
            $scope.response = response;
        },
    )

    $scope.roleTitle = function(role) {
        let title = role.permission;
    
        if (role.scope_gardens !== undefined && role.scope_gardens !== null && role.scope_gardens.length > 0){
          title += ", Gardens = " + role.scope_gardens;
        }
    
        if (role.scope_namespaces !== undefined && role.scope_namespaces !== null && role.scope_namespaces.length > 0){
          title += ", Namespaces = " + role.scope_namespaces;
        }
    
        if (role.scope_systems !== undefined && role.scope_systems !== null && role.scope_systems.length > 0){
          title += ", Systems = " + role.scope_systems;
        }
    
        if (role.scope_instances !== undefined && role.scope_instances !== null && role.scope_instances.length > 0){
          title += ", Instances = " + role.scope_instances;
        }
    
        if (role.scope_versions !== undefined && role.scope_versions !== null && role.scope_versions.length > 0){
          title += ", Versions = " + role.scope_versions;
        }
    
        if (role.scope_commands !== undefined && role.scope_commands !== null && role.scope_commands.length > 0){
          title += ", Commands = " + role.scope_commands;
        }
    
        return title;
      }

}