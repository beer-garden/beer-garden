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

  $scope.doCreate = function(role) {
    const modalInstance = $uibModal.open({
      controller: 'NewRoleController',
      size: 'lg',
      template: template,
      backdrop: 'static',
      resolve: {
        isNew: true,
        editRole: role,
      },
    });
    modalInstance.result.then(
      (create) => {
        RoleService.createRole(create).then($scope.loadRoles);
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
      backdrop: 'static',
      resolve: {
        isNew: true,
        editRole: role,
      },
    });

    modalInstance.result.then(
        (create) => {
          RoleService.createRole(create).then($scope.loadRoles);
        },
        // We don't really need to do anything if canceled
        () => {},
    );
  };

  $scope.doEdit = function(role) {
    const modalInstance = $uibModal.open({
      controller: 'NewRoleController',
      size: 'lg',
      template: template,
      backdrop: 'static',
      resolve: {
        isNew: false,
        editRole: role,
      },
    });

    modalInstance.result.then(
        (create) => {
          RoleService.editRole(create).then($scope.loadRoles);
        },
        // We don't really need to do anything if canceled
        () => {},
    );
  };

  $scope.doDelete = function(role) {
    RoleService.deleteRole(role.name).then($scope.loadRoles);
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

  $scope.loadRoles = function () {
    $scope.alerts = [];
    RoleService.getRoles().then($scope.successCallback, $scope.failureCallback);
  }

  $scope.$on('userChange', () => {
    $scope.response = undefined;
    $scope.loadRoles();
  });

  $scope.loadRoles();
}

newRoleController.$inject = ['$rootScope', '$scope', '$uibModalInstance', 'isNew', 'editRole'];

/**
 * newRoleController - New Role controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export function newRoleController($rootScope, $scope, $uibModalInstance, isNew, editRole = {}) {
  

  $scope.convertScopeToModal = function(scope_values){
    let scopes = [];

    if (scope_values !== undefined && scope_values != null && scope_values.length > 0){
      for (const value of scope_values){
        scopes.push({"scope":value});
      }
    }

    return scopes;
  }

  $scope.convertRoleToModal = function(convertRole){
    let role = angular.copy(convertRole);
    role.scope_gardens = $scope.convertScopeToModal(role.scope_gardens);
    role.scope_namespaces = $scope.convertScopeToModal(role.scope_namespaces);
    role.scope_systems = $scope.convertScopeToModal(role.scope_systems);
    role.scope_versions = $scope.convertScopeToModal(role.scope_versions);
    role.scope_instances = $scope.convertScopeToModal(role.scope_instances);
    role.scope_commands = $scope.convertScopeToModal(role.scope_commands);
    return role;
  }

  $scope.convertScopeFromModal = function(scope_values){
    let scopes = [];

    if (scope_values !== undefined && scope_values != null && scope_values.length > 0){
      for (const value of scope_values){
        if (value.scope !== undefined && value.scope != null && value.scope.length > 0){ 
          scopes.push(value.scope);
        }
      }
    }

    return scopes;
  }

  $scope.convertRoleFromModal = function(convertRole){
    let role = angular.copy(convertRole);
    role.scope_gardens = $scope.convertScopeFromModal(role.scope_gardens);
    role.scope_namespaces = $scope.convertScopeFromModal(role.scope_namespaces);
    role.scope_systems = $scope.convertScopeFromModal(role.scope_systems);
    role.scope_versions = $scope.convertScopeFromModal(role.scope_versions);
    role.scope_instances = $scope.convertScopeFromModal(role.scope_instances);
    role.scope_commands = $scope.convertScopeFromModal(role.scope_commands);
    return role;
  }

  $scope.editRole = $scope.convertRoleToModal(editRole);

  if (isNew) {
    $scope.editRole.name = null;
    $scope.editRole.id = null;
    $scope.editRole.description = null;
  }

  $scope.garden = $rootScope.garden;

  $scope.gardenValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }
    if (garden.name == value) {
      return true;
    }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.gardenValidation(value, child)) {
          return true;
        }
      }
    }

    return false;
  }

  $scope.roleContainsGarden = function (gardenName) {

    if ($scope.editRole.scope_gardens === undefined || $scope.editRole.scope_gardens == null || $scope.editRole.scope_gardens.length == 0) {
      return true;
    }

    let matched = true;
    for (const scope_garden of $scope.editRole.scope_gardens) {
      if (scope_garden.scope !== undefined && scope_garden.scope != null && scope_garden.scope.length > 0) {
        matched = false;
        if (scope_garden.scope == gardenName) {
          return true;
        }
      }
    }
    return matched;
  }

  $scope.namespaceValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    if ($scope.roleContainsGarden(garden.name)) {
      for (const system of garden.systems) {
        if (system.namespace == value) {
          return true;
        }
      }
    }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.namespaceValidation(value, child)) {
          return true;
        }
      }
    }

    return false;
  }

  $scope.roleContainsNamespace = function (namespace) {

    if ($scope.editRole.scope_namespaces === undefined || $scope.editRole.scope_namespaces == null || $scope.editRole.scope_namespaces.length == 0) {
      return true;
    }

    let matched = true;
    for (const scope_namespace of $scope.editRole.scope_namespaces) {
      if (scope_namespace.scope !== undefined && scope_namespace.scope != null && scope_namespace.scope.length > 0) {
        matched = false;
        if (scope_namespace.scope == namespace) {
          return true;
        }
      }
    }
    return matched;
  }

  $scope.systemValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    if ($scope.roleContainsGarden(garden.name)) {
      for (const system of garden.systems) {
        if ($scope.roleContainsNamespace(system.namespace)) {
          if (system.name == value) {
            return true;
          }
        }
      }
    }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.systemValidation(value, child)) {
          return true;
        }
      }
    }

    return false;
  }

  $scope.roleContainsSystem = function (systemName) {

    if ($scope.editRole.scope_systems === undefined || $scope.editRole.scope_systems == null || $scope.editRole.scope_systems.length == 0) {
      return true;
    }

    let matched = true;
    for (const scope_system of $scope.editRole.scope_systems) {
      if (scope_system.scope !== undefined && scope_system.scope != null && scope_system.scope.length > 0) {
        matched = false;
        if (scope_system.scope == systemName) {
          return true;
        }
      }
    }
    return matched;
  }

  $scope.versionValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    if ($scope.roleContainsGarden(garden.name)) {
      for (const system of garden.systems) {
        if ($scope.roleContainsNamespace(system.namespace) && $scope.roleContainsSystem(system.name)) {
          if (system.version == value) {
            return true;
          }
        }
      }
    }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.versionValidation(value, child)) {
          return true;
        }
      }
    }

    return false;
  }

  $scope.roleContainsVersion = function (version) {

    if ($scope.editRole.scope_versions === undefined || $scope.editRole.scope_versions == null || $scope.editRole.scope_versions.length == 0) {
      return true;
    }

    let matched = true;
    for (const scope_version of $scope.editRole.scope_versions) {
      if (scope_version.scope !== undefined && scope_version.scope != null && scope_version.scope.length > 0) {
        matched = false;
        if (scope_version.scope == version) {
          return true;
        }
      }
    }
    return matched;
  }

  $scope.instanceValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    if ($scope.roleContainsGarden(garden.name)) {
      for (const system of garden.systems) {
        if ($scope.roleContainsNamespace(system.namespace) && $scope.roleContainsSystem(system.name) && $scope.roleContainsVersion(system.version)) {
          for (const instance of system.instances) {
            if (instance.name == value) {
              return true;
            }
          }
        }
      }
    }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.instanceValidation(value, child)) {
          return true;
        }
      }
    }

    return false;
  }

  $scope.roleContainsInstance = function (instances) {

    if ($scope.editRole.scope_instances === undefined || $scope.editRole.scope_instances == null || $scope.editRole.scope_instances.length == 0) {
      return true;
    }

    let matched = true;
    for (const scope_instance of $scope.editRole.scope_instances) {
      if (scope_instance.scope !== undefined && scope_instance.scope != null && scope_instance.scope.length > 0) {
        matched = false;
        for (const instance of instances) {
          if (scope_instance.scope == instance) {
            return true;
          }
        }
      }
    }
    return matched;
  }

  $scope.commandsValidation = function (value) {
    return true;
  }
  $scope.commandValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    if ($scope.roleContainsGarden(garden.name)) {
      for (const system of garden.systems) {
        if ($scope.roleContainsNamespace(system.namespace) && $scope.roleContainsSystem(system.name) && $scope.roleContainsVersion(system.version) && $scope.roleContainsInstance(system.instances)) {
          for (const command of system.commands) {
            if (command.name == value) {
              return true;
            }
          }
        }
      }
    }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.commandValidation(value, child)) {
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
        readonly: !isNew,
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
          type: "object",
          properties: {
            scope: { type: "string" },
          }
      }
      },
      scope_versions: {
        title: 'Versions',
        type: 'array',
        items: {
          type: "object",
          properties: {
            scope: { type: "string" },
          }
      }
      },
      scope_instances: {
        title: 'Instances',
        type: 'array',
        items: {
          type: "object",
          properties: {
            scope: { type: "string" },
          }
      }
      },
      scope_commands: {
        title: 'Commands',
        type: 'array',
        items: {
          type: "object",
          properties: {
            scope: { type: "string" },
          }
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
    {
      key: 'scope_systems',
      type: 'array',
      add: "Add System Scope",
      style: {
        add: "btn-success"
      },
      items: [
        {
          key: "scope_systems[].scope",
          validationMessage: {
            'systemValidator': 'Unable to find Namespace in Garden/Namespace Scope'
          },
          $validators: {
            systemValidator: function(value) {
              return $scope.systemValidation(value);
            }
          }
        }
      ],
    },
    {
      key: 'scope_versions',
      type: 'array',
      add: "Add Version Scope",
      style: {
        add: "btn-success"
      },
      items: [
        {
          key: "scope_versions[].scope",
          validationMessage: {
            'versionValidator': 'Unable to find Namespace in Garden/Namespace/System Scope'
          },
          $validators: {
            versionValidator: function(value) {
              return $scope.versionValidation(value);
            }
          }
        }
      ],
    },
    {
      key: 'scope_instances',
      type: 'array',
      add: "Add Instance Scope",
      style: {
        add: "btn-success"
      },
      items: [
        {
          key: "scope_instances[].scope",
          validationMessage: {
            'instanceValidator': 'Unable to find Namespace in Garden/Namespace/System/Version Scope'
          },
          $validators: {
            instanceValidator: function(value) {
              return $scope.instanceValidation(value);
            }
          }
        }
      ],
    },
    {
      key: 'scope_commands',
      type: 'array',
      add: "Add Command Scope",
      style: {
        add: "btn-success"
      },
      items: [
        {
          key: "scope_commands[].scope",
          validationMessage: {
            'commandValidator': 'Unable to find Namespace in Garden/Namespace/System/Version/Instance Scope'
          },
          $validators: {
            commandValidator: function(value) {
              return $scope.commandValidation(value);
            }
          }
        }
      ],
    },
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
              type: 'button',
              style: 'btn-success w-10',
              title: 'Submit',
              onClick: 'submitRole()',
            },
          ],
        },
      ],
    },
  ];

  const generateRoleForm = function() {
    $scope.roleSchema = roleSchema;
    $scope.roleForm = roleForm;
    $scope.$broadcast('schemaFormRedraw');
  };

  // $scope.forceValidation = function() {
  //   $scope.$broadcast('schemaFormValidate');
  //   $scope.$broadcast('schemaForm.error.scope_commands.scope','commandValidator',false);
  // }

  generateRoleForm();

  $scope.submitRole = function() {
    $uibModalInstance.close($scope.convertRoleFromModal($scope.editRole));
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
}
