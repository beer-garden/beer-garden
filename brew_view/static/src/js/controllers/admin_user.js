import _ from 'lodash';
import {arrayToMap, mapToArray} from '../services/utility_service.js';

import template from '../../templates/new_user.html';

adminUserController.$inject = [
  '$scope',
  '$q',
  '$uibModal',
  'RoleService',
  'UserService',
  'PermissionService',
];

/**
 * adminUserController - System management controller.
 * @param  {$scope} $scope            Angular's $scope object.
 * @param  {$scope} $q                Angular's $q object.
 * @param  {$scope} $uibModal         Angular UI's $uibModal object.
 * @param  {Object} RoleService       Beer-Garden's role service object.
 * @param  {Object} UserService       Beer-Garden's user service object.
 * @param  {Object} PermissionService Beer-Garden's permission service object.
 */
export function adminUserController(
    $scope,
    $q,
    $uibModal,
    RoleService,
    UserService,
    PermissionService) {
  $scope.setWindowTitle('users');

  // This holds the raw responses from the backend
  $scope.raws = {};

  // This is the list that gets changed as the user interacts
  $scope.users = [];

  // This is used for comparing changes
  $scope.serverUsers = [];

  // This is the user that's currently under selection
  $scope.selectedUser = {};

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

  $scope.doUpdate = function() {
    let userId = $scope.selectedUser.id;
    let original = _.find($scope.serverUsers, {'id': userId});
    let promises = [];

    let originalList = mapToArray(original.primaryRoles);
    let changedList = mapToArray($scope.selectedUser.primaryRoles);

    let additions = _.difference(changedList, originalList);
    let removals = _.difference(originalList, changedList);

    if (additions.length) {
      promises.push(UserService.addRoles(userId, additions));
    }
    if (removals.length) {
      promises.push(UserService.removeRoles(userId, removals));
    }

    $q.all(promises).then(loadUsers, $scope.addErrorAlert);
  };

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

  $scope.color = function(userId, path) {
    // Pull the correct users based on the current selected user's id
    let originalSelectedUser = _.find($scope.serverUsers, {'id': userId});
    let changedSelectedUser = _.find($scope.users, {'id': userId});

    // Now pull the original and changed values out
    let originalValue = _.get(originalSelectedUser, path);
    let changedValue = _.get(changedSelectedUser, path);

    if (changedValue && !originalValue) {
      return {'color': 'green'};
    } else if (!changedValue && originalValue) {
      return {'color': 'red'};
    }

    return {};
  };

  $scope.isRoleDisabled = function(roleName) {
    // Roles need to be disabled if it's enabled because it's nested
    return $scope.selectedUser.roles[roleName] &&
      $scope.selectedUser.nestedRoles[roleName];
  };

  $scope.roleChange = function(roleName) {
    let changed = $scope.selectedUser;

    // Since this is a result of a click, we need to update primary roles
    changed.primaryRoles[roleName] = changed.roles[roleName];

    // Then get the list of roles that are checked
    let primaryRoleNames = mapToArray(changed.primaryRoles);

    // Now we need the actual role definitions for those roles...
    let primaryRoleList = _.filter($scope.raws.roles, (value, key, collection) => {
      return _.indexOf(primaryRoleNames, value.name) !== -1;
    });

    // ...so that we can calculate nested permissions...
    let coalesced = RoleService.coalescePermissions(primaryRoleList);
    let permissionNames = coalesced[1];

    // Finally, convert that list back into the map angular wants
    let permissionMap = arrayToMap(permissionNames, $scope.raws.permissions);
    changed.permissions = permissionMap;


    // Now deal with roles too
    let allRoleNames = coalesced[0];
    let nestedRoleNames = _.difference(allRoleNames, primaryRoleNames);

    let roleMap = arrayToMap(allRoleNames, $scope.roleNames);
    changed.roles = roleMap;

    let nestedRoleMap = arrayToMap(nestedRoleNames, $scope.roleNames);
    changed.nestedRoles = nestedRoleMap;
  };

  /**
   * handleUsersResponse - Parse and translate users response
   * @param  {Object} response The response
   */
  function handleUsersResponse(response) {
    $scope.raws.users = response.data;

    let thaUsers = [];

    for (let user of $scope.raws.users) {
      let primaryRoleNames = _.map(user.roles, 'name');

      let coalesced = RoleService.coalescePermissions(user.roles);

      let allRoleNames = coalesced[0];

      let nestedRoleNames = _.difference(allRoleNames, primaryRoleNames);
      let allPermissionNames = coalesced[1];

      let roleMap = arrayToMap(allRoleNames, $scope.roleNames);
      let permissionMap = arrayToMap(allPermissionNames, $scope.raws.permissions);

      let primaryRoleMap = arrayToMap(primaryRoleNames, $scope.roleNames);
      let nestedRoleMap = arrayToMap(nestedRoleNames, $scope.roleNames);

      thaUsers.push({
        id: user.id,
        username: user.username,

        roles: roleMap,
        permissions: permissionMap,

        primaryRoles: primaryRoleMap,
        nestedRoles: nestedRoleMap,
      });
    }

    // This is super annoying, but I can't find a better way
    // Save off the current selection ID so we can keep it selected
    let selectedId = $scope.selectedUser['id'];
    let selectedUser = undefined;

    $scope.serverUsers = _.cloneDeep(thaUsers);
    $scope.users = _.cloneDeep(thaUsers);

    if (selectedId) {
      selectedUser = _.find($scope.users, {'id': selectedId});
    }
    $scope.selectedUser = selectedUser || $scope.users[0];
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
      permissions: PermissionService.getPermissions(),
      roles: RoleService.getRoles(),
      users: UserService.getUsers(),
    }).then(
      (responses) => {
        // Success callback is only invoked if all promises are resolved, so just
        // pick one to let the fetch-data directive know about the success
        $scope.response = responses.users;

        $scope.raws = {
          permissions: responses.permissions.data,
          roles: responses.roles.data,
          users: responses.users.data,
        };

        $scope.roleNames = _.map($scope.raws.roles, 'name');
        $scope.permissions = _.groupBy($scope.raws.permissions, (value) => {
          return value.split('-').slice(0, 2).join('-');
        });

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
