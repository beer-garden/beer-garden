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
    RoleService) {
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

  $scope.new_namespace = "";
  $scope.new_access = "";

  $scope.fixed_missing_permissions = false;

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

  $scope.canEdit = function(){
    return $scope.selectedRole.name == 'bg-admin' || $scope.selectedRole.name == 'bg-anonymous' || $scope.selectedRole.name == 'bg-plugin';
  }

  $scope.injectCurrentRole = function(response){

    let role = response.data;

    for (let i = 0; i < $scope.roles.length; i++){
      if ($scope.roles[i].id == role.id){
        $scope.roles[i] = role
        $scope.selectedRole = role
        break;
      }
    }
  }

  $scope.updatePermission = function(permission){

    if (("id" in $scope.selectedRole) && permission.access != null){

        RoleService.addPermission($scope.selectedRole.id, permission)
               .then($scope.injectCurrentRole , $scope.addErrorAlert);

    }
  }

  $scope.removePermission = function(permission){
    RoleService.removePermission($scope.selectedRole.id, permission)
               .then($scope.injectCurrentRole , $scope.addErrorAlert);
  }

  $scope.addPermission = function(){

    if (!("id" in $scope.selectedRole)){
        $scope.alerts.push({
          type: 'danger',
          msg: "Must select Role before adding Permission",
        });
    }
    else if ($scope.new_access == "" || $scope.new_access == null){
        $scope.alerts.push({
          type: 'danger',
          msg: "Must select Access before adding Permission",
        });
    }
    else{
    $scope.updatePermission({"namespace": $scope.new_namespace,
                                 "access":$scope.new_access,
                                 "is_local":($scope.new_namespace == "" || $scope.new_namespace == null)})
    }

  }

  // This is the worst/best solution I could come up with, reload the data.
  // Have to do this, else the ng-repeat removes the Permissions on the first model selected
  $scope.checkPermissionsBug = function(){
    if (!$scope.fixed_missing_permissions){
        $scope.fixed_missing_permissions = true;
        loadAll();
    }

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

  /**
   * loadAll - load everything this controller needs
   */
  function loadAll() {
    $scope.alerts = [];
    $scope.new_permission = null;
    $scope.new_access = null;


    RoleService.getRoles().then(
        $scope.successCallback,
        $scope.failureCallback)

  };

  $scope.successCallback = function(response) {
    $scope.response = response;

    $scope.roles = response.data;

    let selectedId = $scope.selectedRole['id'];
    let selectedRole = {};

    if (selectedId) {
      selectedRole = _.find($scope.roles, {'id': selectedId});
    }

    $scope.selectedRole = selectedRole

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
