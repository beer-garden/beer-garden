import _ from 'lodash';

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

  $scope.doUpdate = function(roleId, newRoles, newPermissions) {
    // newRoles, newPermissions are objects with name -> boolean mapping
    // This transforms them into arrays
    let roleList = _.transform(newRoles, (accumulator, value, key, obj) => {
      if (value) { accumulator.push(key); }
    }, []);
    let permissionList = _.transform(newPermissions, (accumulator, value, key, obj) => {
      if (value) { accumulator.push(key); }
    }, []);

    // Send the update and then reload
    $q.all([
      RoleService.setRoles(roleId, roleList),
      RoleService.setPermissions(roleId, permissionList)
    ]).then(loadAll);
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

  $scope.isDisabled = function(nestedRoleName) {
    return $scope.selectedRole.name === nestedRoleName;
  };

  $scope.roleChange = function(user) {
    // Whenever a role changes we need to recalculate permissions
    let roleList = _.filter($scope.raws.roles, value => {
      return user.roles[value.name];
    });
    let newPermissions = RoleService.coalesce_permissions(roleList)[1];

    let userPermissions = {};
    for (let permission of $scope.raws.permissions) {
      userPermissions[permission] = _.indexOf(newPermissions, permission) !== -1;
    }

    user.permissions = userPermissions;
  };

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
        let nestedRoleNames = _.map(role.roles, 'name');

        let nestedRoles = {};
        for (let roleName of $scope.roleNames) {
          nestedRoles[roleName] = _.indexOf(nestedRoleNames, roleName) !== -1;
        }

        // let nestedPermissionList = RoleService.coalesce_permissions(user.roles)[1];
        let primaryPermissionList = role.permissions;

        let rolePermissions = {};
        for (let permission of $scope.raws.permissions) {
          rolePermissions[permission] = _.indexOf(primaryPermissionList, permission) !== -1;
        }

        thaRoles.push({
          id: role.id,
          name: role.name,
          roles: nestedRoles,
          permissions: rolePermissions,
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
