import _ from 'lodash';

adminUserViewController.$inject = [
  '$scope',
  '$state',
  '$stateParams',
  'RoleService',
  'UserService',
];

/**
 * adminUserViewController - Garden management controller.
 * @param  {Object} $scope           Angular's $scope object.
 * @param  {Object} $state           Angular's $state object.
 * @param  {Object} $stateParams     State params
 * @param  {Object} RoleService      Beer-Garden's role service object.
 * @param  {Object} UserService      Beer-Garden's user service object.
 */
export default function adminUserViewController(
    $scope,
    $state,
    $stateParams,
    RoleService,
    UserService,
) {
  $scope.setWindowTitle('Manage User');
  $scope.alerts = [];

  $scope.doDelete = function(userName) {
    UserService.deleteUser(userName).then(
        $state.go('base.user_admin'),
        failureCallback,
    );
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.submitUserForm = function(form, model) {
    clearScopeAlerts();
    model = blankRequiredFields(model);
    $scope.$broadcast('schemaFormValidate');

    if (form.$valid) {
      UserService.updateUser($scope.data.username, model).then(
          addSuccessAlert,
          addErrorAlert,
      );
    }
  };

  const blankRequiredFields = function(model) {
    // ASF appears to have a bug when using required fields with arrays
    // that makes it possible to get into a non-submittable state when the
    // required fields are defined on the form. Instead, we require the fields
    // on the model, and then just blank out the identifiers that shouldn't
    // be present for the currently selected scope. The backend drops blank
    // identifiers for us anyway.
    model.role_assignments.forEach((assignment) => {
      if (assignment.domain.scope === 'Global') {
        assignment.domain.identifiers.name = '';
      }
      if (assignment.domain.scope !== 'System') {
        assignment.domain.identifiers.namespace = '';
        assignment.domain.identifiers.version = '';
      }
    });

    return model;
  };

  const successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;

    generateUserSF();
  };

  const failureCallback = function(response) {
    $scope.response = response;
    $scope.data = [];
  };

  const addErrorAlert = function(response) {
    $scope.alerts.push({
      type: 'danger',
      msg:
        'Something went wrong on the backend: ' +
        _.get(response, 'data.message', 'Please check the server logs'),
    });
  };

  const addSuccessAlert = function(response) {
    $scope.alerts.push({
      type: 'success',
      msg: 'Saved',
    });
  };

  const clearScopeAlerts = function() {
    while ($scope.alerts.length) {
      $scope.alerts.pop();
    }
  };

  const loadRoleNames = function() {
    return RoleService.getRoles().then((response) => {
      $scope.roleNames = _.map(response.data.roles, 'name');
    });
  };

  const loadUser = function() {
    $scope.response = undefined;
    $scope.data = [];

    return UserService.getUser($stateParams.username).then(
        successCallback,
        failureCallback,
    );
  };

  const generateUserSF = function() {
    $scope.userSchema = roleAssignmentSchema;
    $scope.userForm = roleAssignmentForm;
    $scope.userModel = serverModelToForm($scope.data);

    // This gets set here because $scope.roleNames is not yet set at
    // roleAssignmentSchema declaration time
    $scope.userSchema.properties.role_assignments.items.properties.role_name.enum =
      $scope.roleNames;

    $scope.$broadcast('schemaFormRedraw');
  };

  const roleAssignmentSchema = {
    type: 'object',
    properties: {
      role_assignments: {
        title: 'Role Assignments',
        type: 'array',
        items: {
          type: 'object',
          title: ' ',
          required: ['role_name'],
          properties: {
            role_name: {
              title: 'Role',
              type: 'string',
            },
            domain: {
              title: ' ',
              type: 'object',
              required: ['scope'],
              properties: {
                scope: {
                  title: 'Scope',
                  type: 'string',
                  enum: ['Global', 'Garden', 'System'],
                },
                identifiers: {
                  title: 'Scope Identifiers',
                  type: 'object',
                  required: ['namespace', 'name'],
                  properties: {
                    namespace: {
                      type: 'string',
                    },
                    name: {
                      type: 'string',
                    },
                    version: {
                      type: 'string',
                    },
                  },
                },
              },
            },
          },
        },
      },
    },
  };

  const roleAssignmentForm = [
    {
      key: 'role_assignments',
      add: 'Add',
      style: {add: 'btn-default'},
      items: [
        'role_assignments[].role_name',
        {
          type: 'section',
          htmlClass: 'row',
          items: [
            {
              type: 'section',
              htmlClass: 'col-xs-2',
              items: ['role_assignments[].domain.scope'],
            },
            {
              type: 'section',
              htmlClass: 'col-xs-2',
              condition:
                'model.role_assignments[arrayIndex].domain.scope === "System"',
              items: ['role_assignments[].domain.identifiers.namespace'],
            },
            {
              type: 'section',
              htmlClass: 'col-xs-2',
              condition:
                'model.role_assignments[arrayIndex].domain.scope !== "Global"',
              items: ['role_assignments[].domain.identifiers.name'],
            },
            {
              type: 'section',
              htmlClass: 'col-xs-2',
              condition:
                'model.role_assignments[arrayIndex].domain.scope === "System"',
              items: ['role_assignments[].domain.identifiers.version'],
            },
          ],
        },
      ],
    },
    {
      type: 'submit',
      style: 'btn-primary w-10',
      title: 'Save',
    },
  ];

  const serverModelToForm = function(model) {
    model.role_assignments.forEach((assignment) => {
      assignment.role_name = assignment.role.name;
    });

    return model;
  };

  loadRoleNames().then(loadUser());
}
