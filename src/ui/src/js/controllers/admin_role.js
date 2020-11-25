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
    PermissionService) {
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
    let modalInstance = $uibModal.open({
      controller: 'NewRoleController',
      size: 'sm',
      template: template,
    });

    modalInstance.result.then(
      (create) => {
        RoleService.createRole(create).then(loadAll);
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
      let originalList = mapToArray(original.primaryRoles);
      let changedList = mapToArray($scope.selectedRole.primaryRoles);

      let additions = _.difference(changedList, originalList);
      let removals = _.difference(originalList, changedList);

      if (additions.length) {
        promises.push(RoleService.addRoles(roleId, additions));
      }
      if (removals.length) {
        promises.push(RoleService.removeRoles(roleId, removals));
      }
    } else if ($scope.selectedRole.permissionsChanged) {
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

    $q.all(promises).then(loadAll, $scope.addErrorAlert);
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

  $scope.roleChange = function(roleName) {
    let changed = $scope.selectedRole;
    let original = _.find($scope.serverRoles, {'id': changed.id});

  };

  /**
   * loadAll - load everything this controller needs
   */
  function loadAll() {
    $scope.alerts = [];

    RoleService.getRoles().then(
        $scope.successCallback,
        $scope.failureCallback)

  };

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.roles = response.data;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };


  $scope.$on('userChange', () => {
    $scope.response = undefined;
    loadAll();
  });

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

  $scope.ok = function() {
    $uibModalInstance.close($scope.create);
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
};
