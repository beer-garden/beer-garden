import _ from 'lodash';
import {arrayToMap, mapToArray} from '../services/utility_service.js';

import template from '../../templates/new_user.html';

adminUserController.$inject = [
  '$scope',
  '$q',
  '$uibModal',
  'RoleService',
  'UserService',
];

/**
 * adminUserController - System management controller.
 * @param  {$scope} $scope            Angular's $scope object.
 * @param  {$scope} $q                Angular's $q object.
 * @param  {$scope} $uibModal         Angular UI's $uibModal object.
 * @param  {Object} RoleService       Beer-Garden's role service object.
 * @param  {Object} UserService       Beer-Garden's user service object.
 */
export function adminUserController(
    $scope,
    $q,
    $uibModal,
    RoleService,
    UserService) {
  $scope.setWindowTitle('users');

  // This holds the raw responses from the backend
  $scope.raws = {};

  // This is the list that gets changed as the user interacts
  $scope.users = [];

  $scope.roles = []

  $scope.selectedPermissions = []

  // This is used for comparing changes
  $scope.serverUsers = [];

  // This is the user that's currently under selection
  $scope.selectedUser = {};

  $scope.selectedRoles = {};

  // Normal loader
  $scope.loader = {};

  $scope.doCreate = function() {
    let modalInstance = $uibModal.open({
      controller: 'NewUserController',
      size: 'sm',
      template: template,
    });

    modalInstance.result.then(
      (create) => {
        if (create.password === create.verify) {
          UserService.createUser(create.username, create.password).then(loadUsers);
        }
      },
      // We don't really need to do anything if canceled
      () => {}
    );
  };

  $scope.doDelete = function(userId) {
    UserService.deleteUser(userId).then(loadUsers);
  };

  $scope.doReset = function(userId) {
    let original = _.find($scope.serverUsers, {'id': userId});
    let changed = _.find($scope.users, {'id': userId});

    changed.roles = _.cloneDeep(original.roles);
    changed.permissions = _.cloneDeep(original.permissions);
  };

  $scope.updateRole = function(roleName){
    let changed = $scope.selectedUser;
    let roleStatus = $scope.selectedRoles[roleName]

    for(let i = 0; i < changed.roles.length; i++){
        if (roleName == changed.roles[i].name){
            if (roleStatus){
                return;
            }
            else{
                UserService.removeRole($scope.selectedUser.id, changed.roles[i].id);
                loadUsers();
                return;
            }
        }
    }

    if (roleStatus){
        for (let i = 0; i < $scope.raws.roles.length; i++){
            if (roleName == $scope.raws.roles[i].name){
                UserService.addRole($scope.selectedUser.id, $scope.raws.roles[i].id);
                loadUsers();
                return;
            }
        }
    }
    // Does Nothing
  }


  $scope.addErrorAlert = function(response) {
    $scope.alerts.push({
      type: 'danger',
      msg: 'Something went wrong on the backend: ' +
        _.get(response, 'data.message', 'Please check the server logs'),
    });
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.setRoles = function(){
    let changed = $scope.selectedUser;

    $scope.selectedRoles = {}

    for (let i = 0; i < $scope.raws.roles; i++){
        $scope.selectedRoles[$scope.raws.roles[i].name] = false;
    }

    for (let i = 0; i < changed.roles.length; i++){
        $scope.selectedRoles[changed.roles[i].name] = true;
    }

    $scope.selectedPermissions = RoleService.consolidatePermissions($scope.selectedUser.roles)
  }

  /**
   * handleUsersResponse - Parse and translate users response
   * @param  {Object} response The response
   */
  function handleUsersResponse(response) {
    $scope.raws.users = response.data;

    let thaUsers = [];

    // This is super annoying, but I can't find a better way
    // Save off the current selection ID so we can keep it selected
    let selectedId = $scope.selectedUser['id'];
    let selectedUser = undefined;

    $scope.serverUsers = _.cloneDeep($scope.raws.users);
    $scope.users = _.cloneDeep($scope.raws.users);

    if (selectedId) {
      selectedUser = _.find($scope.users, {'id': selectedId});
    }
    $scope.selectedUser = selectedUser || $scope.users[0];

    $scope.setRoles()
  }

  /**
   * loadUsers - load all users
   */
  function loadUsers() {
    UserService.getUsers().then(handleUsersResponse);
  }

  /**
   * loadAll - load everything this controller needs
   */
  function loadAll() {
    $scope.alerts = [];

    $q.all({
      roles: RoleService.getRoles(),
      users: UserService.getUsers(),
    }).then(
      (responses) => {
        // Success callback is only invoked if all promises are resolved, so just
        // pick one to let the fetch-data directive know about the success
        $scope.response = responses.users;

        $scope.raws = {
          roles: responses.roles.data,
          users: responses.users.data,
        };

        $scope.roleNames = _.map($scope.raws.roles, 'name');

        $scope.roles = $scope.raws.roles

        handleUsersResponse(responses.users);

        $scope.loader.loaded = true;
        $scope.loader.error = false;
        $scope.loader.errorMessage = undefined;
      },
      (response) => {
        $scope.response = response;
      }
    );
  };

  $scope.$on('userChange', () => {
    $scope.response = undefined;
    loadAll();
  });

  loadAll();
};

newUserController.$inject = [
  '$scope',
  '$uibModalInstance',
];

/**
 * newUserController - New User controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export function newUserController($scope, $uibModalInstance) {
  $scope.create = {};

  $scope.ok = function() {
    $uibModalInstance.close($scope.create);
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
};
