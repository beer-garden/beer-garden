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
    clearUserFormState(model);

    $scope.$broadcast('schemaFormValidate');

    if (form.$valid) {
      if (
        (model.new_password || model.confirm_password) &&
        model.new_password !== model.confirm_password
      ) {
        $scope.$broadcast(
            'schemaForm.error.confirm_password',
            'passwordMatch',
            false,
        );
      } else {
        if (model.new_password) {
          model.password = model.new_password;
        }
        UserService.updateUser($scope.data.username, model).then(
            addSuccessAlert,
            addErrorAlert,
        );
      }
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
        assignment.domain.identifiers = {name: ''};
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
    $scope.displaySyncStatus = (Object.keys($scope.data.sync_status).length > 0);

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

  const clearUserFormState = function(model) {
    model = blankRequiredFields(model);
    model.password = undefined;

    $scope.$broadcast(
        'schemaForm.error.confirm_password',
        'passwordMatch',
        true,
    );

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
    $scope.userSchema = userSchema;
    $scope.userForm = userForm;
    $scope.userModel = serverModelToForm($scope.data);

    // This gets set here because $scope.roleNames is not yet set at
    // userSchema declaration time
    $scope.userSchema.properties.role_assignments.items.properties.role_name.enum =
      $scope.roleNames;

    $scope.$broadcast('schemaFormRedraw');
  };

  const userSchema = {
    type: 'object',
    properties: {
      new_password: {
        type: 'string',
      },
      confirm_password: {
        type: 'string',
      },
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

  const userForm = [
    {
      type: 'section',
      htmlClass: 'row',
      items: [
        {
          type: 'section',
          htmlClass: 'col-xs-2',
          items: [
            {
              type: 'password',
              key: 'new_password',
              title: 'Change Password',
              placeholder: 'password',
              disableSuccessState: true,
            },
          ],
        },
      ],
    },
    {
      type: 'section',
      htmlClass: 'row',
      items: [
        {
          type: 'section',
          htmlClass: 'col-xs-2',
          items: [
            {
              type: 'password',
              key: 'confirm_password',
              notitle: true,
              placeholder: 'confirm password',
              disableSuccessState: true,
              validationMessage: {
                passwordMatch: 'Passwords do not match',
              },
            },
          ],
        },
      ],
    },
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
