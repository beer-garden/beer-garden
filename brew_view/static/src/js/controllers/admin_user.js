import _ from 'lodash';

import template from '../../templates/new_user.html';

adminUserController.$inject = [
  '$scope',
  '$q',
  '$uibModal',
  'RoleService',
  'UserService',
  'PermissionService',
];

/**
 * adminUserController - System management controller.
 * @param  {$scope} $scope            Angular's $scope object.
 * @param  {$scope} $q                Angular's $q object.
 * @param  {$scope} $uibModal         Angular UI's $uibModal object.
 * @param  {Object} RoleService       Beer-Garden's role service object.
 * @param  {Object} UserService       Beer-Garden's user service object.
 * @param  {Object} PermissionService Beer-Garden's permission service object.
 */
export function adminUserController(
    $scope,
    $q,
    $uibModal,
    RoleService,
    UserService,
    PermissionService) {
  // This holds the raw responses from the backend
  $scope.raws = {};

  // This is the list that gets changed as the user interacts
  $scope.users = [];

  // This is used for comparing changes
  $scope.serverUsers = [];

  $scope.doCreate = function() {
    let modalInstance = $uibModal.open({
      template: template,
      controller: 'NewUserController',
    });

    modalInstance.result.then(
      create => {
        if (create.password === create.verify) {
          UserService.createUser(create.username, create.password).then(loadUsers);
        }
      },
      // We don't really need to do anything if canceled
      () => {}
    );
  };

  $scope.doDelete = function(userId) {
    UserService.deleteUser(userId).then(loadUsers);
  };

  $scope.doUpdate = function(userId, newRoles) {
    // newRoles is an object with roleName -> boolean mapping
    // This transform creates an array of 'true' roles
    let roleList = _.transform(newRoles, (accumulator, value, key, obj) => {
      if (value) { accumulator.push(key); }
    }, []);

    // Send the update and then reload the user definitions
    UserService.setRoles(userId, roleList).then(loadUsers);
  };

  $scope.color = function(userId, path) {
    // Pull the correct users based on the current selected user's id
    let originalSelectedUser = _.find($scope.serverUsers, {'id': userId});
    let changedSelectedUser = _.find($scope.users, {'id': userId});

    // Now pull the original and changed values out
    let originalValue = _.get(originalSelectedUser, path);
    let changedValue = _.get(changedSelectedUser, path);

    if (changedValue && !originalValue) {
      return {'color': 'green'};
    }
    else if (!changedValue && originalValue) {
      return {'color': 'red'};
    }

    return {};
  };

  $scope.roleChange = function(user) {
    // Whenever a role changes we need to recalculate permissions
    let roleList = _.filter($scope.raws.roles, value => {
      return user.roles[value.name];
    });
    let newPermissions = RoleService.coalesce_permissions(roleList)[1];

    let userPermissions = {};
    for (let permission of $scope.raws.permissions) {
      userPermissions[permission] = _.indexOf(newPermissions, permission) !== -1;
    }

    user.permissions = userPermissions;
  };

  function handleUsersResponse(response) {
    $scope.raws.users = response.data;

    let thaUsers = [];

    for (let user of $scope.raws.users) {
      let userRoleNames = _.map(user.roles, 'name');

      let userRoles = {};
      for (let roleName of $scope.roleNames) {
        userRoles[roleName] = _.indexOf(userRoleNames, roleName) !== -1;
      }

      let userPermissionList = RoleService.coalesce_permissions(user.roles)[1];

      let userPermissions = {};
      for (let permission of $scope.raws.permissions) {
        userPermissions[permission] = _.indexOf(userPermissionList, permission) !== -1;
      }

      thaUsers.push({
        id: user.id,
        username: user.username,
        roles: userRoles,
        permissions: userPermissions,
      });
    }

    $scope.serverUsers = _.cloneDeep(thaUsers);
    $scope.users = _.cloneDeep(thaUsers);

    // TODO - This would be nice, but issues
    // $scope.selectedUser = $scope.users[0];
  }

  function loadUsers() {
    UserService.getUsers().then(handleUsersResponse);
  }

  function loadAll() {
    $q.all({
      permissions: PermissionService.getPermissions(),
      roles: RoleService.getRoles(),
      users: UserService.getUsers(),
    })
    .then(responses => {
      $scope.raws = {
        permissions: responses.permissions.data,
        roles: responses.roles.data,
        users: responses.users.data,
      };

      $scope.roleNames = _.map($scope.raws.roles, "name");
      $scope.permissions = _.groupBy($scope.raws.permissions, value => {
        return value.split('-').slice(0, 2).join('-');
      });

      handleUsersResponse(responses.users);
    });
  };

  loadAll();
};

newUserController.$inject = [
  '$scope',
  '$uibModalInstance',
];

/**
 * newUserController - System management controller.
 * @param  {$scope} $scope                        Angular's $scope object.
 * @param  {$uibModalInstance} $uibModalInstance  Angular UI's $uibModalInstance object.
 */
export function newUserController($scope, $uibModalInstance) {
  $scope.create = {};

  $scope.ok = function () {
    $uibModalInstance.close($scope.create);
  };

  $scope.cancel = function () {
    $uibModalInstance.dismiss('cancel');
  };
};
