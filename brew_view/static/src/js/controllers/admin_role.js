import _ from 'lodash';
import {arrayToMap, mapToArray} from '../services/utility_service.js';

import template from '../../templates/new_role.html';

adminRoleController.$inject = [
  '$scope',
  '$q',
  '$uibModal',
  'RoleService',
  'PermissionService',
];

/**
 * adminRoleController - System management controller.
 * @param  {$scope} $scope            Angular's $scope object.
 * @param  {$scope} $q                Angular's $q object.
 * @param  {$scope} $uibModal         Angular UI's $uibModal object.
 * @param  {Object} RoleService       Beer-Garden's role service object.
 * @param  {Object} PermissionService Beer-Garden's permission service object.
 */
export function adminRoleController(
    $scope,
    $q,
    $uibModal,
    RoleService,
    PermissionService) {
  // This holds the raw responses from the backend
  $scope.raws = {};

  // This is the list that gets changed as the user interacts
  $scope.roles = [];

  // This is used for comparing changes
  $scope.serverRoles = [];

  // This is the role that's currently under selection
  $scope.selectedRole = {};

  $scope.doCreate = function() {
    let modalInstance = $uibModal.open({
      template: template,
      controller: 'NewRoleController',
    });

    modalInstance.result.then(
      create => {
        RoleService.createRole(create.name).then(loadAll);
      },
      // We don't really need to do anything if canceled
      () => {}
    );
  };

  $scope.doDelete = function(roleId) {
    RoleService.deleteRole(roleId).then(loadAll);
  };

  $scope.doReset = function(roleId) {
    let original = _.find($scope.serverRoles, {'id': roleId});
    let changed = _.find($scope.roles, {'id': roleId});

    changed.roles = _.cloneDeep(original.roles);
    changed.permissions = _.cloneDeep(original.permissions);
  };

  $scope.doUpdate = function() {
    let roleId = $scope.selectedRole.id;
    let original = _.find($scope.serverRoles, {'id': roleId});
    let promises = [];

    if ($scope.selectedRole.rolesChanged) {
      let originalList = mapToArray(original.roles);
      let changedList = mapToArray($scope.selectedRole.roles);

      let additions = _.difference(changedList, originalList);
      let removals = _.difference(originalList, changedList);

      if (additions.length) {
        promises.push(RoleService.addRoles(roleId, additions));
      }
      if (removals.length) {
        promises.push(RoleService.removeRoles(roleId, removals));
      }
    }
    else if ($scope.selectedRole.permissionsChanged) {
      let originalList = mapToArray(original.permissions);
      let changedList = mapToArray($scope.selectedRole.permissions);

      let additions = _.difference(changedList, originalList);
      let removals = _.difference(originalList, changedList);

      if (additions.length) {
        promises.push(RoleService.addPermissions(roleId, additions));
      }
      if (removals.length) {
        promises.push(RoleService.removePermissions(roleId, removals));
      }
    }

    $q.all(promises).then(loadAll);
  };

  $scope.color = function(roleId, path) {
    // Pull the correct users based on the current selected user's id
    let originalSelected = _.find($scope.serverRoles, {'id': roleId});
    let changedSelected = _.find($scope.roles, {'id': roleId});

    // Now pull the original and changed values out
    let originalValue = _.get(originalSelected, path);
    let changedValue = _.get(changedSelected, path);

    if (changedValue && !originalValue) {
      return {'color': 'green'};
    }
    else if (!changedValue && originalValue) {
      return {'color': 'red'};
    }

    return {};
  };

  $scope.isRoleDisabled = function(nestedRoleName) {
    // Roles need to be disabled if a permission is changed
    // or the role is enabled as a result of a double-nested role
    // or the role is the actual role being modified
    return $scope.selectedRole.permissionsChanged ||
      $scope.selectedRole.nestedRoles[nestedRoleName] ||
      $scope.selectedRole.name === nestedRoleName;
  };

  $scope.isPermissionDisabled = function(nestedPermissionName) {
    // Permissions need to be disabled if a role is changed
    // or the permission is enabled as a result of a nested role
    return $scope.selectedRole.rolesChanged ||
      $scope.selectedRole.nestedPermissions[nestedPermissionName];
  };

  $scope.roleChange = function(roleId) {
    let original = _.find($scope.serverRoles, {'id': roleId});
    let changed = _.find($scope.roles, {'id': roleId});

    changed.rolesChanged = false;
    for (let key in changed.roles) {
      if (changed.roles[key] != original.roles[key]) {
       changed.rolesChanged = true;
      }
    }

    // Ok, so if a role is changing that means that the 'primary' permissions
    // have not changed. So recalculate the coalesced permissions (the
    // permissions that are a result of nested roles) and then add the primary
    // permissions back
    // First, let's get the list of primary permissions
    let primaryPermissionNames = mapToArray(changed.primaryPermissions);

    // Then get the list of roles that are checked
    let nestedRoleNames = mapToArray(changed.roles);

    // Now we need the actual role definitions for those roles...
    let nestedRoleList = _.filter($scope.raws.roles, (value, key, collection) => {
      return _.indexOf(nestedRoleNames, value.name) !== -1;
    });

    // ...so that we can calculate nested permissions...
    let nestedPermissionNames = RoleService.coalesce_permissions(nestedRoleList)[1];

    // And then combine them into one big list o' permissions
    let allPermissionNames = _.union(primaryPermissionNames, nestedPermissionNames);

    // Finally, convert that list back into the map angular wants
    let permissionMap = arrayToMap(allPermissionNames, $scope.raws.permissions);
    changed.permissions = permissionMap;
  };

  $scope.permissionChange = function(roleId) {
    let original = _.find($scope.serverRoles, {'id': roleId});
    let changed = _.find($scope.roles, {'id': roleId});

    changed.permissionsChanged = false;
    for (let key in changed.permissions) {
      if (changed.permissions[key] != original.permissions[key]) {
       changed.permissionsChanged = true;
      }
    }
  }

  function loadAll() {
    $q.all({
      permissions: PermissionService.getPermissions(),
      roles: RoleService.getRoles(),
    })
    .then(responses => {
      $scope.raws = {
        permissions: responses.permissions.data,
        roles: responses.roles.data,
      };

      $scope.roleNames = _.map($scope.raws.roles, "name");
      $scope.permissions = _.groupBy($scope.raws.permissions, value => {
        return value.split('-').slice(0, 2).join('-');
      });

      // Load into the form we can work with
      let thaRoles = [];

      for (let role of $scope.raws.roles) {
        // Need to make a distinction between roles / permissions that are
        // attached to this role (that will be editable) and those that are
        // inherited because of nested roles

        let primaryRoleNames = _.map(role.roles, 'name');
        let primaryPermissionNames = role.permissions;

        let coalesced = RoleService.coalesce_permissions(role.roles);

        let allRoleNames = coalesced[0];
        let nestedPermissionNames = coalesced[1];

        let nestedRoleNames = _.difference(allRoleNames, primaryRoleNames);
        let allPermissionNames = _.union(primaryPermissionNames, coalesced[1]);

        let roleMap = arrayToMap(allRoleNames, $scope.roleNames);
        let permissionMap = arrayToMap(allPermissionNames, $scope.raws.permissions);

        let primaryRoleMap = arrayToMap(primaryRoleNames, $scope.roleNames);
        let primaryPermissionMap = arrayToMap(primaryPermissionNames, $scope.raws.permissions);

        let nestedRoleMap = arrayToMap(nestedRoleNames, $scope.roleNames);
        let nestedPermissionMap = arrayToMap(nestedPermissionNames, $scope.raws.permissions);

        thaRoles.push({
          id: role.id,
          name: role.name,

          roles: roleMap,
          permissions: permissionMap,

          primaryRoles: primaryRoleMap,
          primaryPermissions: primaryPermissionMap,

          nestedRoles: nestedRoleMap,
          nestedPermissions: nestedPermissionMap,

          rolesChanged: false,
          permissionsChanged: false,
        });
      }

      // This is super annoying, but I can't find a better way
      // Save off the current selection ID so we can keep it selected
      let selectedId = $scope.selectedRole['id'];

      $scope.serverRoles = _.cloneDeep(thaRoles);
      $scope.roles = _.cloneDeep(thaRoles);

      if (selectedId) {
        $scope.selectedRole = _.find($scope.roles, {'id': selectedId});
      }
      else {
        $scope.selectedRole = $scope.roles[0];
      }
    });
  };

  loadAll();
};

newRoleController.$inject = [
  '$scope',
  '$uibModalInstance',
];

/**
 * newRoleController - New Role controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export function newRoleController($scope, $uibModalInstance) {
  $scope.create = {};

  $scope.ok = function () {
    $uibModalInstance.close($scope.create);
  };

  $scope.cancel = function () {
    $uibModalInstance.dismiss('cancel');
  };
};
