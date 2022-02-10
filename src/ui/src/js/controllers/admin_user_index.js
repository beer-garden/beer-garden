import template from '../../templates/new_user.html';

adminUserIndexController.$inject = ['$scope', '$uibModal', 'UserService'];

/**
 * adminUserIndexController - Controller for the job index page.
 * @param  {Object} $scope        Angular's $scope object.
 * @param  {$scope} $uibModal     Angular UI's $uibModal object.
 * @param  {Object} UserService   Beer-Garden's job service.
 */
export function adminUserIndexController($scope, $uibModal, UserService) {
  $scope.setWindowTitle('users');

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = {};
  };

  $scope.doCreate = function() {
    const modalInstance = $uibModal.open({
      controller: 'NewUserController',
      size: 'sm',
      template: template,
    });

    modalInstance.result.then(
        (create) => {
          if (create.password === create.verify) {
            UserService.createUser(create.username, create.password).then(
                loadUsers,
            );
          }
        },
        // We don't really need to do anything if canceled
        () => {},
    );
  };

  function loadUsers() {
    $scope.response = undefined;
    $scope.data = {};

    UserService.getUsers().then($scope.successCallback, $scope.failureCallback);
  }

  $scope.$on('userChange', () => {
    loadUsers();
  });

  loadUsers();
}

newUserController.$inject = ['$scope', '$uibModalInstance'];

/**
 * newUserController - New User controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export function newUserController($scope, $uibModalInstance) {
  $scope.create = {};

  $scope.ok = function() {
    $uibModalInstance.close($scope.create);
  };

  $scope.cancel = function() {
    $uibModalInstance.dismiss('cancel');
  };
}
