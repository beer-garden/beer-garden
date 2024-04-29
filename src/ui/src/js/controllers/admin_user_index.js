import newUserTemplate from '../../templates/new_user.html';
import syncUsersTemplate from '../../templates/sync_users.html';
import addRemoveRoles from '../../templates/add_remove_roles.html';

adminUserIndexController.$inject = ['$scope', '$uibModal', 'UserService', 'TokenService'];

/**
 * adminUserIndexController - Controller for the user index page.
 * @param  {Object} $scope        Angular's $scope object.
 * @param  {$scope} $uibModal     Angular UI's $uibModal object.
 * @param  {Object} UserService   Beer-Garden's user service.
 * @param  {Object} TokenService   Beer-Garden's token service.
 */
export default function adminUserIndexController($scope, $uibModal, UserService, TokenService) {
  $scope.setWindowTitle('users');

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.users = response.data;
    $scope.displaySyncStatus = false;
    // setUserFullySynced();
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.users = [];
  };

  $scope.maxPermission = function(user) {

    let permission = "NONE";

    for (const role of user.local_roles){
      if (role.permission == "GARDEN_ADMIN"){
        return "GARDEN_ADMIN";
      }
      else if (role.permission == "PLUGIN_ADMIN" && ["NONE", "READ_ONLY", "OPERATOR"].includes(permission)){
        permission = role.permission
      }
      else if (role.permission == "OPERATOR" && ["NONE", "READ_ONLY"].includes(permission)){
        permission = role.permission
      }
      else if (role.permission == "READ_ONLY" && ["NONE"].includes(permission)){
        permission = role.permission
      }
    }

    for (const role of user.remote_roles){
      if (role.permission == "GARDEN_ADMIN"){
        return "GARDEN_ADMIN";
      }
      else if (role.permission == "PLUGIN_ADMIN" && ["NONE", "READ_ONLY", "OPERATOR"].includes(permission)){
        permission = role.permission
      }
      else if (role.permission == "OPERATOR" && ["NONE", "READ_ONLY"].includes(permission)){
        permission = role.permission
      }
      else if (role.permission == "READ_ONLY" && ["NONE"].includes(permission)){
        permission = role.permission
      }
    }

    return permission;
  }

  $scope.getLastAuth = function (user) {

    if (user.metadata === undefined || user.metadata.last_authentication === undefined || user.metadata.last_authentication === null ){
      return "NEVER"
    }
    return formatDate(user.metadata.last_authentication);
  }

  $scope.roleTitle = function(role) {
    let title = role.permission;

    if (role.scope_gardens.length > 0){
      title += ", Gardens = " + role.scope_gardens;
    }

    if (role.scope_namespaces.length > 0){
      title += ", Namespaces = " + role.scope_namespaces;
    }

    if (role.scope_systems.length > 0){
      title += ", Systems = " + role.scope_systems;
    }

    if (role.scope_instances.length > 0){
      title += ", Instances = " + role.scope_instances;
    }

    if (role.scope_versions.length > 0){
      title += ", Versions = " + role.scope_versions;
    }

    if (role.scope_commands.length > 0){
      title += ", Commands = " + role.scope_commands;
    }

    return title;
  }

  $scope.rolesList = function(roles) {
    let rolesDisplay = null;

    for (const role of roles) {
      if (rolesDisplay == null) {
        rolesDisplay = "<div title='test'>" + role.name + "</div>";
      } else {
        rolesDisplay = rolesDisplay + ", " + role.name;
      }
    }

    return rolesDisplay;
  }

  $scope.doDelete = function(user) {
    UserService.deleteUser(user.username).then(
      loadUsers,
    );
  };

  $scope.doRevokeToken = function(user) {
    TokenService.revokeUserToken(user.username).then(
      loadUsers,
    );
  };

  $scope.doCreate = function() {
    const modalInstance = $uibModal.open({
      controller: 'NewUserController',
      size: 'sm',
      template: newUserTemplate,
    });

    modalInstance.result.then(
        (create) => {
          if (create.password === create.confirm) {
            UserService.createUser(create.username, create.password).then(
                loadUsers,
            );
          }
        },
        // We don't really need to do anything if canceled
        () => {},
    );
  };

  $scope.showLogs = function(user) {
    
    $uibModal.open({
      template: addRemoveRoles,
      resolve: {
        user: user,
      },
      controller: 'addRemoveRolesController',
      windowClass: 'app-modal-window',
    });
    
  };

  $scope.doSync = function() {
    $uibModal.open({
      controller: 'SyncUsersController',
      size: 'md',
      template: syncUsersTemplate,
    }).result.then(() => {
      loadUsers();
    }, () => {
      loadUsers();
    });
  };

  const loadUsers = function() {
    $scope.response = undefined;
    $scope.users = [];

    UserService.getUsers().then($scope.successCallback, $scope.failureCallback);
  };

  // const setUserFullySynced = function() {
  //   $scope.users.forEach((user) => {
  //     user.fullySynced = true;

  //     if (user.sync_status) {
  //       Object.values(user.sync_status).forEach((synced) => {
  //         // If we get here at all, then there is sync data and we'll want
  //         // to render it, so set that here. If we never get here, that means
  //         // there are no remote gardens, so showing the sync status would be
  //         // meaningless.
  //         $scope.displaySyncStatus = true;

  //         if (!synced) {
  //           user.fullySynced = false;
  //         }
  //       });
  //     }
  //   });
  // };

  $scope.$on('userChange', () => {
    loadUsers();
  });

  loadUsers();
}
