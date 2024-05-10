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
      size: 'lg',
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
    RoleService.getRoles().then($scope.successCallback, $scope.failureCallback);
  }

  $scope.$on('userChange', () => {
    $scope.response = undefined;
    loadRoles();
  });

  loadRoles();
}

newRoleController.$inject = ['$rootScope', '$scope', '$uibModalInstance', 'create'];

/**
 * newRoleController - New Role controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export function newRoleController($rootScope, $scope, $uibModalInstance, create = {}) {
  $scope.create = angular.copy(create);
  $scope.garden = $rootScope.garden;

  $scope.gardenValidation = function(value, garden = null) {
    if (value === undefined || value == null || value.length == 0){
      return true;
    }
    if (garden == null){
        garden = $scope.garden;
    }
    if (garden.name == value){
        return true;
    }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0){
      for (const child of garden.children) {
          if ($scope.gardenValidation(value, child)){
              return true;
          }
      }
    }

    return false;
  }

  $scope.roleContainsGarden = function(garden){

    if ($scope.create.scope_gardens === undefined || $scope.create.scope_gardens == null || $scope.create.scope_gardens.length == 0){
      return true;
    }

    let matched = true;
    for (const scope_garden of $scope.create.scope_gardens){
      if (scope_garden.scope.length > 0){
        matched = false;
        if (scope_garden.scope == garden.name){
          return true;
        }
      }
    }
    return matched;
  }

  $scope.namespaceValidation = function(value, garden = null) {
    if (value === undefined || value == null || value.length == 0){
      return true;
    }
    if (garden == null){
        garden = $scope.garden;
    }

    if ($scope.roleContainsGarden(garden)) {
      for (const system of garden.systems){
        if (system.namespace == value){
          return true;
        }
      }
    }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0){
      for (const child of garden.children) {
          if ($scope.namespaceValidation(value, child)){
              return true;
          }
      }
    }

    return false;
  }

  const roleSchema = {
    type: 'object',
    required: ['name', 'permission'],
    properties: {
      name: {
        title: 'Name',
        minLength: 1,
        type: 'string',
      },
      description: {
        title: 'Description',
        type: 'string',
      },
      permission: {
        title: 'Permission',
        type: 'string',
        enum: ["GARDEN_ADMIN","PLUGIN_ADMIN","OPERATOR","READ_ONLY"],
      },
      scope_gardens: {
        title: 'Gardens',
        type: 'array',
        items: {

            type: "object",
            properties: {
              scope: { type: "string" },
            }
        }
      },
      scope_namespaces: {
        title: 'Namespaces',
        type: 'array',
        items: {

            type: "object",
            properties: {
              scope: { type: "string" },
            }
        }
      },
      scope_systems: {
        title: 'Systems',
        type: 'array',
        items: {
          type: 'string',
          notitle: true
        }
      },
      scope_versions: {
        title: 'Versions',
        type: 'array',
        items: {
          type: 'string',
          notitle: true
        }
      },
      scope_instances: {
        title: 'Instances',
        type: 'array',
        items: {
          type: 'string',
          notitle: true
        }
      },
      scope_commands: {
        title: 'Commands',
        type: 'array',
        items: {
          type: 'string',
          notitle: true
        }
      },
    },
  };

  const roleForm = [
    "name",
    "description",
    "permission",
    {
      key: 'scope_gardens',
      type: 'array',
      add: "Add Garden Scope",
      style: {
        add: "btn-success"
      },
      items: [
        {
          key: "scope_gardens[].scope",
          validationMessage: {
            'gardenValidator': 'Unable to find Garden'
          },
          $validators: {
            gardenValidator: function(value) {
              return $scope.gardenValidation(value);
            }
          }
        }
      ],
    },
    {
      key: 'scope_namespaces',
      type: 'array',
      add: "Add Namespace Scope",
      style: {
        add: "btn-success"
      },
      items: [
        {
          key: "scope_namespaces[].scope",
          validationMessage: {
            'namespaceValidator': 'Unable to find Namespace in Garden Scope'
          },
          $validators: {
            namespaceValidator: function(value) {
              return $scope.namespaceValidation(value);
            }
          }
        }
      ],
    },
    "scope_systems",
    "scope_versions",
    "scope_instances",
    "scope_commands",
    {
      type: 'section',
      htmlClass: 'row',
      items: [
        {
          type: 'section',
          htmlClass: 'col-xs-3 col-md-offset-5',
          items: [
            {
              type: 'button',
              style: 'btn-danger w-10',
              title: 'Cancel',
              onClick: 'cancel()',
            },
          ],
        },
        {
          type: 'section',
          htmlClass: 'col-xs-4',
          items: [
            {
              type: 'submit',
              style: 'btn-success w-10',
              title: 'Submit',
            },
          ],
        },
      ],
    },
  ];

  const generateChangePasswordForm = function() {
    $scope.roleSchema = roleSchema;
    $scope.roleForm = roleForm;
    $scope.$broadcast('schemaFormRedraw');
  };

  // $scope.$broadcast('schemaFormValidate');
  generateChangePasswordForm();

  $scope.ok = function() {
    $uibModalInstance.close($scope.create);
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
}
