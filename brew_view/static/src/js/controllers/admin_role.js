import _ from 'lodash';

import template from '../../templates/new_role.html';

adminRoleController.$inject = [
  '$scope',
  '$q',
  '$uibModal',
  'RoleService',
  'PermissionService',
  'UtilityService',
];

/**
 * adminRoleController - System management controller.
 * @param  {$scope} $scope            Angular's $scope object.
 * @param  {$scope} $q                Angular's $q object.
 * @param  {$scope} $uibModal         Angular UI's $uibModal object.
 * @param  {Object} RoleService       Beer-Garden's role service object.
 * @param  {Object} PermissionService Beer-Garden's permission service object.
 * @param  {Object} UtilityService    Beer-Garden's utility service object.
 */
export function adminRoleController(
    $scope,
    $q,
    $uibModal,
    RoleService,
    PermissionService,
    UtilityService) {
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

    if ($scope.selectedRole.rolesChanged) {
      let roleList = UtilityService.mapToArray($scope.selectedRole.roles);
      RoleService.setRoles($scope.selectedRole.id, roleList).then(loadAll);
    }
    else if ($scope.selectedRole.permissionsChanged) {
      let original = _.find($scope.serverRoles, {'id': roleId});

      let originalList = UtilityService.mapToArray(original.permissions);
      let changedList = UtilityService.mapToArray($scope.selectedRole.permissions);

      let additions = _.difference(changedList, originalList);
      let removals = _.difference(originalList, changedList);

      let promises = [];
      if (additions.length) {
        promises.push(RoleService.addPermissions(roleId, additions));
      }
      if (removals.length) {
        promises.push(RoleService.removePermissions(roleId, removals));
      }

      $q.all(promises).then(loadAll);
    }
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
    return $scope.selectedRole.permissionsChanged ||
      $scope.selectedRole.name === nestedRoleName;
  };

  $scope.isPermissionDisabled = function(nestedRoleName) {
    return $scope.selectedRole.rolesChanged;
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
    let primaryPermissionNames = UtilityService.mapToArray(changed.primaryPermissions);

    // Then get the list of roles that are checked
    let nestedRoleNames = UtilityService.mapToArray(changed.roles);

    // Now we need the actual role definitions for those roles...
    let nestedRoleList = _.filter($scope.raws.roles, (value, key, collection) => {
      return _.indexOf(nestedRoleNames, value.name) !== -1;
    });

    // ...so that we can calculate nested permissions...
    let nestedPermissionNames = RoleService.coalesce_permissions(nestedRoleList)[1];

    // And then combine them into one big list o' permissions
    let allPermissionNames = _.union(primaryPermissionNames, nestedPermissionNames);

    // Finally, convert that list back into the map angular wants
    let permissionMap = UtilityService.arrayToMap(allPermissionNames, $scope.raws.permissions);
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
        let allPermissionNames = _.union(primaryPermissionNames, coalesced[1]);

        let roleMap = UtilityService.arrayToMap(allRoleNames, $scope.roleNames);
        let permissionMap = UtilityService.arrayToMap(allPermissionNames, $scope.raws.permissions);

        let primaryRoleMap = UtilityService.arrayToMap(primaryRoleNames, $scope.roleNames);
        let primaryPermissionMap = UtilityService.arrayToMap(primaryPermissionNames, $scope.raws.permissions);

        thaRoles.push({
          id: role.id,
          name: role.name,
          roles: roleMap,
          permissions: permissionMap,
          primaryRoles: primaryRoleMap,
          primaryPermissions: primaryPermissionMap,

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
