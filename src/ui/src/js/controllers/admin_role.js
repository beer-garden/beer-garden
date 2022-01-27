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
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $q                Angular's $q object.
 * @param  {Object} $uibModal         Angular UI's $uibModal object.
 * @param  {Object} RoleService       Beer-Garden's role service object.
 * @param  {Object} PermissionService Beer-Garden's permission service object.
 */
export function adminRoleController(
    $scope,
    $q,
    $uibModal,
    RoleService,
    PermissionService,
) {
  $scope.setWindowTitle('roles');

  // This holds the raw responses from the backend
  $scope.raws = {};

  // This is the list that gets changed as the user interacts
  $scope.roles = [];

  // This is used for comparing changes
  $scope.serverRoles = [];

  // This is the role that's currently under selection
  $scope.selectedRole = {};

  // Normal loader
  $scope.loader = {};

  $scope.doCreate = function() {
    const modalInstance = $uibModal.open({
      controller: 'NewRoleController',
      size: 'sm',
      template: template,
    });

    modalInstance.result.then(
        (create) => {
          RoleService.createRole(create).then(loadAll);
        },
        // We don't really need to do anything if canceled
        () => {},
    );
  };

  $scope.doDelete = function(roleId) {
    RoleService.deleteRole(roleId).then(loadAll);
  };

  $scope.doReset = function(roleId) {
    const original = _.find($scope.serverRoles, {id: roleId});
    const changed = _.find($scope.roles, {id: roleId});

    changed.roles = _.cloneDeep(original.roles);
    changed.permissions = _.cloneDeep(original.permissions);
  };

  $scope.doUpdate = function() {
    const roleId = $scope.selectedRole.id;
    const original = _.find($scope.serverRoles, {id: roleId});
    const promises = [];

    if ($scope.selectedRole.rolesChanged) {
      const originalList = mapToArray(original.primaryRoles);
      const changedList = mapToArray($scope.selectedRole.primaryRoles);

      const additions = _.difference(changedList, originalList);
      const removals = _.difference(originalList, changedList);

      if (additions.length) {
        promises.push(RoleService.addRoles(roleId, additions));
      }
      if (removals.length) {
        promises.push(RoleService.removeRoles(roleId, removals));
      }
    } else if ($scope.selectedRole.permissionsChanged) {
      const originalList = mapToArray(original.permissions);
      const changedList = mapToArray($scope.selectedRole.permissions);

      const additions = _.difference(changedList, originalList);
      const removals = _.difference(originalList, changedList);

      if (additions.length) {
        promises.push(RoleService.addPermissions(roleId, additions));
      }
      if (removals.length) {
        promises.push(RoleService.removePermissions(roleId, removals));
      }
    }

    $q.all(promises).then(loadAll, $scope.addErrorAlert);
  };

  $scope.addErrorAlert = function(response) {
    $scope.alerts.push({
      type: 'danger',
      msg:
        'Something went wrong on the backend: ' +
        _.get(response, 'data.message', 'Please check the server logs'),
    });
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.color = function(roleId, path) {
    // Pull the correct users based on the current selected user's id
    const originalSelected = _.find($scope.serverRoles, {id: roleId});
    const changedSelected = _.find($scope.roles, {id: roleId});

    // Now pull the original and changed values out
    const originalValue = _.get(originalSelected, path);
    const changedValue = _.get(changedSelected, path);

    if (changedValue && !originalValue) {
      return {color: 'green'};
    } else if (!changedValue && originalValue) {
      return {color: 'red'};
    }

    return {};
  };

  $scope.isRoleDisabled = function(nestedRoleName) {
    // Roles need to be disabled if a permission is changed
    // or the role is enabled as a result of a double-nested role
    // or the role is the actual role being modified
    return (
      $scope.selectedRole.permissionsChanged ||
      $scope.selectedRole.nestedRoles[nestedRoleName] ||
      $scope.selectedRole.name === nestedRoleName
    );
  };

  $scope.isPermissionDisabled = function(nestedPermissionName) {
    // Permissions need to be disabled if a role is changed
    // or the permission is enabled as a result of a nested role
    return (
      $scope.selectedRole.rolesChanged ||
      $scope.selectedRole.nestedPermissions[nestedPermissionName]
    );
  };

  $scope.roleChange = function(roleName) {
    const changed = $scope.selectedRole;
    const original = _.find($scope.serverRoles, {id: changed.id});

    // Since this is a result of a click, we need to update primary roles
    changed.primaryRoles[roleName] = changed.roles[roleName];

    // Ok, so if a role is changing that means that the 'primary' permissions
    // have not changed. So recalculate the coalesced permissions (the
    // permissions that are a result of nested roles) and then add the primary
    // permissions back
    // First, let's get the list of primary permissions
    const primaryPermissionNames = mapToArray(changed.primaryPermissions);

    // Then get the list of roles that are checked
    const primaryRoleNames = mapToArray(changed.primaryRoles);

    // Now we need the actual role definitions for those roles...
    const primaryRoleList = _.filter(
        $scope.raws.roles,
        (value, key, collection) => {
          return _.indexOf(primaryRoleNames, value.name) !== -1;
        },
    );

    // ...so that we can calculate nested permissions...
    const coalesced = RoleService.coalescePermissions(primaryRoleList);
    const nestedPermissionNames = coalesced[1];

    // And then combine them into one big list o' permissions
    const allPermissionNames = _.union(
        primaryPermissionNames,
        nestedPermissionNames,
    );

    // Finally, convert that list back into the map angular wants
    const permissionMap = arrayToMap(allPermissionNames, $scope.raws.permissions);
    changed.permissions = permissionMap;

    // Now deal with roles too
    const allRoleNames = coalesced[0];
    const nestedRoleNames = _.difference(allRoleNames, primaryRoleNames);

    const roleMap = arrayToMap(allRoleNames, $scope.roleNames);
    changed.roles = roleMap;

    const nestedRoleMap = arrayToMap(nestedRoleNames, $scope.roleNames);
    changed.nestedRoles = nestedRoleMap;

    // Finally, need to determine if the nested roles have been changed so
    // that we can enable or disable changing the permissions
    changed.rolesChanged = false;
    for (const key in changed.roles) {
      if (changed.roles[key] != original.roles[key]) {
        changed.rolesChanged = true;
      }
    }
  };

  $scope.permissionChange = function(permission) {
    const changed = $scope.selectedRole;
    const original = _.find($scope.serverRoles, {id: changed.id});

    // Since this is a result of a click, we need to update primary permissions
    changed.primaryPermissions[permission] = changed.permissions[permission];

    if (changed.permissions[permission] != original.permissions[permission]) {
      changed.permissionsChanged = true;
    }
  };

  /**
   * loadAll - load everything this controller needs
   */
  function loadAll() {
    $scope.alerts = [];

    $q.all({
      permissions: PermissionService.getPermissions(),
      roles: RoleService.getRoles(),
    }).then(
        (responses) => {
        // Success callback is only invoked if all promises are resolved, so just
        // pick one to let the fetch-data directive know about the success
          $scope.response = responses.roles;

          $scope.raws = {
            permissions: responses.permissions.data,
            roles: responses.roles.data,
          };

          $scope.roleNames = _.map($scope.raws.roles, 'name');
          $scope.permissions = _.groupBy($scope.raws.permissions, (value) => {
            return value.split('-').slice(0, 2).join('-');
          });

          // Load into the form we can work with
          const thaRoles = [];

          for (const role of $scope.raws.roles) {
          // Need to make a distinction between roles / permissions that are
          // attached to this role (that will be editable) and those that are
          // inherited because of nested roles

            const primaryRoleNames = _.map(role.roles, 'name');
            const primaryPermissionNames = role.permissions;

            const coalesced = RoleService.coalescePermissions(role.roles);

            const allRoleNames = coalesced[0];
            const nestedPermissionNames = coalesced[1];

            const nestedRoleNames = _.difference(allRoleNames, primaryRoleNames);
            const allPermissionNames = _.union(
                primaryPermissionNames,
                coalesced[1],
            );

            const roleMap = arrayToMap(allRoleNames, $scope.roleNames);
            const permissionMap = arrayToMap(
                allPermissionNames,
                $scope.raws.permissions,
            );

            const primaryRoleMap = arrayToMap(primaryRoleNames, $scope.roleNames);
            const primaryPermissionMap = arrayToMap(
                primaryPermissionNames,
                $scope.raws.permissions,
            );

            const nestedRoleMap = arrayToMap(nestedRoleNames, $scope.roleNames);
            const nestedPermissionMap = arrayToMap(
                nestedPermissionNames,
                $scope.raws.permissions,
            );

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
          const selectedId = $scope.selectedRole['id'];
          let selectedRole = undefined;

          $scope.serverRoles = _.cloneDeep(thaRoles);
          $scope.roles = _.cloneDeep(thaRoles);

          if (selectedId) {
            selectedRole = _.find($scope.roles, {id: selectedId});
          }
          $scope.selectedRole = selectedRole || $scope.roles[0];

          $scope.loader.loaded = true;
          $scope.loader.error = false;
          $scope.loader.errorMessage = undefined;
        },
        (response) => {
          $scope.response = response;
        },
    );
  }

  $scope.$on('userChange', () => {
    $scope.response = undefined;
    loadAll();
  });

  loadAll();
}

newRoleController.$inject = ['$scope', '$uibModalInstance'];

/**
 * newRoleController - New Role controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export function newRoleController($scope, $uibModalInstance) {
  $scope.create = {};

  $scope.ok = function() {
    $uibModalInstance.close($scope.create);
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
}
