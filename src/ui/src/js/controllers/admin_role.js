import _ from 'lodash';
import {arrayToMap, mapToArray} from '../services/utility_service.js';

import template from '../../templates/new_role.html';

adminRoleController.$inject = [
  '$scope',
  '$q',
  '$uibModal',
  'RoleService',
];

/**
 * adminRoleController - System management controller.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $q                Angular's $q object.
 * @param  {Object} $uibModal         Angular UI's $uibModal object.
 * @param  {Object} RoleService       Beer-Garden's role service object.
 */
export function adminRoleController(
    $scope,
    $q,
    $uibModal,
    RoleService,
) {
  $scope.setWindowTitle('roles');

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

  $scope.doClone = function(role) {
    const modalInstance = $uibModal.open({
      controller: 'NewRoleController',
      size: 'sm',
      template: template,
      resolve: {
        create: role,
      },
    });

    modalInstance.result.then(
        (create) => {
          RoleService.createRole(create).then(loadAll);
        },
        // We don't really need to do anything if canceled
        () => {},
    );
  };

  $scope.doDelete = function(role) {
    RoleService.deleteRole(role.id).then(loadAll);
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

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.roles = response.data;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.roles = [];
  };

  const loadRoles = function () {
    $scope.alerts = [];
    $scope.data = RoleService.getRoles().then($scope.successCallback, $scope.failureCallback);
  }

  $scope.$on('userChange', () => {
    $scope.response = undefined;
    loadRoles();
  });

  loadRoles();
}

newRoleController.$inject = ['$scope', '$uibModalInstance'];

/**
 * newRoleController - New Role controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export function newRoleController($scope, $uibModalInstance, create = {}) {
  $scope.create = create;

  $scope.ok = function() {
    $uibModalInstance.close($scope.create);
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
}
