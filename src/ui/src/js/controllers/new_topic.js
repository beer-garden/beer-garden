newTopicController.$inject = ['$rootScope', '$scope', '$uibModalInstance', 'isNew', 'editTopic'];

/**
 * newRoleController - New Role controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export default function newTopicController($rootScope, $scope, $uibModalInstance, isNew, editTopic = {}) {
  
//   $scope.convertTopicToModal = function(convertTopic){
//     let topic = angular.copy(convertTopic);
//     return topic;
//   };

//   $scope.convertTopicFromModal = function(convertTopic){
//     let topic = angular.copy(convertTopic);
//     return topic;
//   }

  $scope.modalTitle = (isNew) ? "Create Topic" : "Add Subscribers";
  $scope.editTopic = editTopic

  if (isNew) {
    $scope.editTopic.name = null;
    $scope.editTopic.subscribers = [];
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

//   $scope.roleContainsGarden = function (gardenName) {

//     if ($scope.editRole.scope_gardens === undefined || $scope.editRole.scope_gardens == null || $scope.editRole.scope_gardens.length == 0) {
//       return true;
//     }

//     let matched = true;
//     for (const scope_garden of $scope.editRole.scope_gardens) {
//       if (scope_garden.scope !== undefined && scope_garden.scope != null && scope_garden.scope.length > 0) {
//         matched = false;
//         if (scope_garden.scope == gardenName) {
//           return true;
//         }
//       }
//     }
//     return matched;
//   }

  $scope.namespaceValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    // if ($scope.roleContainsGarden(garden.name)) {
    //   for (const system of garden.systems) {
    //     if (system.namespace == value) {
    //       return true;
    //     }
    //   }
    // }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.namespaceValidation(value, child)) {
          return true;
        }
      }
    }

    return false;
  }

//   $scope.roleContainsNamespace = function (namespace) {

//     if ($scope.editRole.scope_namespaces === undefined || $scope.editRole.scope_namespaces == null || $scope.editRole.scope_namespaces.length == 0) {
//       return true;
//     }

//     let matched = true;
//     for (const scope_namespace of $scope.editRole.scope_namespaces) {
//       if (scope_namespace.scope !== undefined && scope_namespace.scope != null && scope_namespace.scope.length > 0) {
//         matched = false;
//         if (scope_namespace.scope == namespace) {
//           return true;
//         }
//       }
//     }
//     return matched;
//   }

  $scope.systemValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    // if ($scope.roleContainsGarden(garden.name)) {
    //   for (const system of garden.systems) {
    //     if ($scope.roleContainsNamespace(system.namespace)) {
    //       if (system.name == value) {
    //         return true;
    //       }
    //     }
    //   }
    // }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.systemValidation(value, child)) {
          return true;
        }
      }
    }

    return false;
  }

//   $scope.roleContainsSystem = function (systemName) {

//     if ($scope.editRole.scope_systems === undefined || $scope.editRole.scope_systems == null || $scope.editRole.scope_systems.length == 0) {
//       return true;
//     }

//     let matched = true;
//     for (const scope_system of $scope.editRole.scope_systems) {
//       if (scope_system.scope !== undefined && scope_system.scope != null && scope_system.scope.length > 0) {
//         matched = false;
//         if (scope_system.scope == systemName) {
//           return true;
//         }
//       }
//     }
//     return matched;
//   }

  $scope.versionValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    // if ($scope.roleContainsGarden(garden.name)) {
    //   for (const system of garden.systems) {
    //     if ($scope.roleContainsNamespace(system.namespace) && $scope.roleContainsSystem(system.name)) {
    //       if (system.version == value) {
    //         return true;
    //       }
    //     }
    //   }
    // }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.versionValidation(value, child)) {
          return true;
        }
      }
    }

    return false;
  }

//   $scope.roleContainsVersion = function (version) {

//     if ($scope.editRole.scope_versions === undefined || $scope.editRole.scope_versions == null || $scope.editRole.scope_versions.length == 0) {
//       return true;
//     }

//     let matched = true;
//     for (const scope_version of $scope.editRole.scope_versions) {
//       if (scope_version.scope !== undefined && scope_version.scope != null && scope_version.scope.length > 0) {
//         matched = false;
//         if (scope_version.scope == version) {
//           return true;
//         }
//       }
//     }
//     return matched;
//   }

  $scope.instanceValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    // if ($scope.roleContainsGarden(garden.name)) {
    //   for (const system of garden.systems) {
    //     if ($scope.roleContainsNamespace(system.namespace) && $scope.roleContainsSystem(system.name) && $scope.roleContainsVersion(system.version)) {
    //       for (const instance of system.instances) {
    //         if (instance.name == value) {
    //           return true;
    //         }
    //       }
    //     }
    //   }
    // }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.instanceValidation(value, child)) {
          return true;
        }
      }
    }

    return false;
  }

//   $scope.roleContainsInstance = function (instances) {

//     if ($scope.editRole.scope_instances === undefined || $scope.editRole.scope_instances == null || $scope.editRole.scope_instances.length == 0) {
//       return true;
//     }

//     let matched = true;
//     for (const scope_instance of $scope.editRole.scope_instances) {
//       if (scope_instance.scope !== undefined && scope_instance.scope != null && scope_instance.scope.length > 0) {
//         matched = false;
//         for (const instance of instances) {
//           if (scope_instance.scope == instance) {
//             return true;
//           }
//         }
//       }
//     }
//     return matched;
//   }

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

//     if ($scope.roleContainsGarden(garden.name)) {
//       for (const system of garden.systems) {
//         if ($scope.roleContainsNamespace(system.namespace) && $scope.roleContainsSystem(system.name) && $scope.roleContainsVersion(system.version) && $scope.roleContainsInstance(system.instances)) {
//           for (const command of system.commands) {
//             if (command.display_name || command.name == value) {
//               return true;
//             }
//           }
//         }
//       }
//     }

    if (garden.children !== undefined && garden.children != null && garden.children.length > 0) {
      for (const child of garden.children) {
        if ($scope.commandValidation(value, child)) {
          return true;
        }
      }
    }

    return false;
  }

  const topicSchema = {
    type: 'object',
    required: ['name'],
    properties: {
      name: {
        title: 'Name',
        minLength: 1,
        type: 'string',
        readonly: !isNew,
      },
      subscribers: {
        title: 'Subscribers',
        type: 'array',
        items: {
            type: "object",
            properties: {
              garden: { type: "string" },
              namespace: { type: "string" },
              system: { type: "string" },
              version: { type: "string" },
              instance: { type: "string" },
              command: { type: "string" },
            }
        }
      },
    },
  };

  const topicForm = [
    "name",
    {
      key: 'subscribers',
      type: 'array',
      add: "Add Subscriber",
      style: {
        add: "btn-success"
      },
      items: [
        {
            key: "subscribers[].garden",
            validationMessage: {
                'gardenValidator': 'Unable to find Garden'
            },
            $validators: {
                gardenValidator: function(value) {
                return $scope.gardenValidation(value);
                }
            }
        },
        {
            key: "subscribers[].namespace",
            validationMessage: {
                'namespaceValidator': 'Unable to find Namespace in Garden Scope'
            },
            $validators: {
                namespaceValidator: function(value) {
                return $scope.namespaceValidation(value);
                }
            }
        },
        {
            key: "subscribers[].system",
            validationMessage: {
              'systemValidator': 'Unable to find Namespace in Garden/Namespace Scope'
            },
            $validators: {
              systemValidator: function(value) {
                return $scope.systemValidation(value);
              }
            }
        },
        {
            key: "subscribers[].version",
            validationMessage: {
              'versionValidator': 'Unable to find Namespace in Garden/Namespace/System Scope'
            },
            $validators: {
              versionValidator: function(value) {
                return $scope.versionValidation(value);
              }
            }
        },
        {
            key: "subscribers[].instance",
            validationMessage: {
              'instanceValidator': 'Unable to find Namespace in Garden/Namespace/System/Version Scope'
            },
            $validators: {
              instanceValidator: function(value) {
                return $scope.instanceValidation(value);
              }
            }
        },
        {
            key: "subscribers[].command",
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
              onClick: 'submitTopic()',
            },
          ],
        },
      ],
    },
  ];

  const generateTopicForm = function() {
    $scope.topicSchema = topicSchema;
    $scope.topicForm = topicForm;
    $scope.$broadcast('schemaFormRedraw');
  };

  // $scope.forceValidation = function() {
  //   $scope.$broadcast('schemaFormValidate');
  //   $scope.$broadcast('schemaForm.error.scope_commands.scope','commandValidator',false);
  // }

  generateTopicForm();

  $scope.submitTopic = function() {
    $uibModalInstance.close($scope.editTopic);
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
}
