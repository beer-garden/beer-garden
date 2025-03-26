newTopicController.$inject = ['$rootScope', '$scope', '$uibModalInstance', 'isNew', 'editTopic'];

/**
 * newRoleController - New Role controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export default function newTopicController($rootScope, $scope, $uibModalInstance, isNew, editTopic = {}) {
  
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

  $scope.namespaceValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    for (const system of garden.systems) {
      if (system.namespace == value) {
        return true;
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

  $scope.systemValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    for (const system of garden.systems) {
      if (system.name == value) {
        return true;
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

  $scope.versionValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    for (const system of garden.systems) {
      if (system.version == value) {
        return true;
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

  $scope.instanceValidation = function (value, garden = null) {
    if (value === undefined || value == null || value.length == 0) {
      return true;
    }
    if (garden == null) {
      garden = $scope.garden;
    }

    for (const system of garden.systems) {
      for (const instance of system.instances) {
        if (instance.name == value) {
          return true;
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

    for (const system of garden.systems) {
      for (const command of system.commands) {
        if (command.display_name || command.name == value) {
          return true;
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

  generateTopicForm();

  $scope.submitTopic = function() {
    $uibModalInstance.close($scope.editTopic);
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
}
