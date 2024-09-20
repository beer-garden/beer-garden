import newUserTemplate from '../../templates/new_user.html';
import syncUsersTemplate from '../../templates/sync_users.html';
import addRemoveRoles from '../../templates/add_remove_roles.html';
import userGardenAccounts from '../../templates/user_garden_account.html';
import changePasswordTemplate from '../../templates/change_password.html';
import {formatDate} from '../services/utility_service.js';

adminUserIndexController.$inject = ['$rootScope', '$scope', '$uibModal', 'UserService', 'TokenService'];

/**
 * adminUserIndexController - Controller for the user index page.
 * @param  {Object} $scope        Angular's $scope object.
 * @param  {$scope} $uibModal     Angular UI's $uibModal object.
 * @param  {Object} UserService   Beer-Garden's user service.
 * @param  {Object} TokenService   Beer-Garden's token service.
 */
export default function adminUserIndexController($rootScope, $scope, $uibModal, UserService, TokenService) {
  $scope.setWindowTitle('users');

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.users = response.data;
    $scope.displaySyncStatus = false;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.users = [];
  };

  $scope.formatDate = formatDate;

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

    for (const role of user.upstream_roles){
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
    return $scope.formatDate(user.metadata.last_authentication);
  }

  $scope.getMissingRoles = function (user) {
   
    if (user.metadata === undefined || user.metadata.last_authentication_headers_local_roles === undefined || user.metadata.last_authentication_headers_local_roles === null ){
      return [];
    }

    let missingRoles = [];
    for (const auth_role of user.metadata.last_authentication_headers_local_roles){
      let isMissing = true;
      for (const user_role of user.local_roles){
        if (user_role.name == auth_role){
          isMissing = false;
          break;
        }
      }

      if (isMissing){
        missingRoles.push(auth_role);
      }

    }
    return missingRoles;
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

  $scope.doRescan = function() {
    UserService.rescan().then(
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

  $scope.showAddRemoveRoles = function(user) {

    $scope.updateUser = user;
    
    $uibModal.open({
      template: addRemoveRoles,
      resolve: {
        user: $scope.updateUser,
      },
      controller: 'addRemoveRolesController',
      windowClass: 'app-modal-window',
    }).result.then(loadUsers);
    
  };

  $scope.showUserGardenAccounts = function(user) {

    $scope.updateUser = user;
    
    $uibModal.open({
      template: userGardenAccounts,
      resolve: {
        user: $scope.updateUser,
      },
      controller: 'userGardenAccountsController',
      windowClass: 'app-modal-window',
    }).result.then(loadUsers);
    
  };

  
  $scope.doAdminChangePassword = function(user) {
    return $uibModal.open({
      template: changePasswordTemplate,
      resolve: {
        user: user,
      },
      controller: 'ChangePasswordAdminController',
      size: 'sm',
      // windowClass: 'app-modal-window',
      
      
    }).result.then(
        _.noop,
        _.noop,
    );
  };

  $scope.doSync = function() {
    $uibModal.open({
      controller: 'SyncUsersController',
      size: 'md',
      template: syncUsersTemplate,
    }).result.then(loadUsers);
  };

  const loadUsers = function() {
    $scope.response = undefined;
    $scope.users = [];

    UserService.getUsers().then($scope.successCallback, $scope.failureCallback);
  };

  $scope.$on('userChange', () => {
    loadUsers();
  });

  loadUsers();
}
