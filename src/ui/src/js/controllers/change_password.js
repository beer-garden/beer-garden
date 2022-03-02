changePasswordController.$inject = ['$scope', '$uibModalInstance', 'UserService'];

/**
 * changePasswordController - Controller for change password modal.
 * @param  {Object} $scope             Angular's $scope object.
 * @param  {$scope} $uibModalInstance  Angular UI's $uibModalInstance object.
 * @param  {Object} UserService        Beer-Garden's user service.
 */
export default function changePasswordController($scope, $uibModalInstance, UserService) {
  $scope.cancel = function() {
    $uibModalInstance.close();
  };

  $scope.submitChangePasswordForm = function(form, model) {
    // Clear previously set errors
    $scope.$broadcast('schemaForm.error.current', 'incorrectPassword', true);
    $scope.$broadcast('schemaForm.error.confirm', 'passwordMatch', true);

    // Run required fields validation
    $scope.$broadcast('schemaFormValidate');

    if (form.$valid) {
      if (model.new === model.confirm) {
        UserService.changePassword(model.current, model.new).then(
            $uibModalInstance.close,
            incorrectPasswordError,
        );
      } else {
        $scope.$broadcast('schemaForm.error.confirm', 'passwordMatch', false);
      }
    }
  };

  const incorrectPasswordError = function() {
    $scope.$broadcast('schemaForm.error.current', 'incorrectPassword', false);
  };

  const changePasswordSchema = {
    type: 'object',
    required: ['current', 'new', 'confirm'],
    properties: {
      current: {
        title: 'Current Password',
        type: 'string',
      },
      new: {
        title: 'New Password',
        type: 'string',
      },
      confirm: {
        title: 'Confirm Password',
        type: 'string',
      },
    },
  };

  const changePasswordForm = [
    {
      type: 'password',
      key: 'current',
      placeholder: 'current password',
      validationMessage: {
        incorrectPassword: 'Current password is incorrect',
      },
    },
    {
      type: 'password',
      key: 'new',
      placeholder: 'new password',
    },
    {
      type: 'password',
      key: 'confirm',
      notitle: true,
      placeholder: 'confirm password',
      validationMessage: {
        passwordMatch: 'Passwords do not match',
      },
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
    $scope.changePasswordSchema = changePasswordSchema;
    $scope.changePasswordForm = changePasswordForm;
    $scope.changePasswordModel = {};

    $scope.$broadcast('schemaFormRedraw');
  };

  generateChangePasswordForm();
}
