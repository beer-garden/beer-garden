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
  $scope.users = [];
  $scope.serverUsers = [];
  $scope.rawPermissions = [];
  $scope.rawRoles = [];
  $scope.showModify = true;

  $scope.doCreate = function() {
    let modalInstance = $uibModal.open({
      template: template,
      controller: 'NewUserController',
    });

    modalInstance.result.then(
      create => {
        if (create.password === create.verify) {
          UserService.createUser(create.username, create.password);
        }
        console.log(username);
      },
      () => {
        console.log('bye');
      }
    );
  };

  $scope.doDelete = function() {
    UserService.deleteUser($scope.currentUser.id);
  };

  $scope.doUpdate = function() {
    let newRoles = _.transform(
      $scope.currentUser.roles,
      (accumulator, value, key, obj) => {
        if (value) {
          accumulator.push(key);
        }
      },
      []
    );
    // let newRoles = _.filter($scope.rawRoles, value => {
    //   return $scope.currentUser.roles[value.name];
    // });
    UserService.setRoles($scope.currentUser.id, newRoles).then(loadAll);

    // Pull the correct user based on the current selected id
    // let currServerUser = _.find($scope.serverUsers,
    //   {'id': $scope.currentUser.id});
    //
    //     let userRoleNames = _.map(user.roles, 'name');
    //
    //     let userRoles = {};
    //     for (let roleName of $scope.roleNames) {
    //       userRoles[roleName] = _.indexOf(userRoleNames, roleName) !== -1;
    //     }
    //
    //     let userPermissionList = RoleService.coalesce_permissions(user.roles)[1];
    //
    //     let userPermissions = {};
    //     for (let permission of $scope.rawPermissions) {
    //       userPermissions[permission] = _.indexOf(userPermissionList, permission) !== -1;
    //     }
    //
    // currServerUser.roles = userRoles;
    // currServerUser.permissions = userPermissions;
  };

  $scope.color = function(path) {
    // Pull the correct user based on the current selected id
    let currServerUser = _.find($scope.serverUsers,
      {'id': $scope.currentUser.id});

    let serverValue = _.get(currServerUser, path);
    let newValue = _.get($scope.currentUser, path);

    if (newValue && !serverValue) {
      return {'color': 'green'};
    }
    else if (!newValue && serverValue) {
      return {'color': 'red'};
    }

    return {};
  };

  $scope.roleChange = function(roleName) {
    let newRoles = _.filter($scope.rawRoles, value => {
      return $scope.currentUser.roles[value.name];
    });
    let newPermissions = RoleService.coalesce_permissions(newRoles)[1];

    let userPermissions = {};
    for (let permission of $scope.rawPermissions) {
      userPermissions[permission] = _.indexOf(newPermissions, permission) !== -1;
    }
    $scope.currentUser.permissions = userPermissions;
  };

  function handleUsersResponse(response) {
    $scope.rawUsers = response.data;
    $scope.users = [];

    let thaUsers = [];

    for (let user of $scope.rawUsers) {
      let userRoleNames = _.map(user.roles, 'name');

      let userRoles = {};
      for (let roleName of $scope.roleNames) {
        userRoles[roleName] = _.indexOf(userRoleNames, roleName) !== -1;
      }

      let userPermissionList = RoleService.coalesce_permissions(user.roles)[1];

      let userPermissions = {};
      for (let permission of $scope.rawPermissions) {
        userPermissions[permission] = _.indexOf(userPermissionList, permission) !== -1;
      }

      thaUsers.push({
        id: user.id,
        username: user.username,
        roles: userRoles,
        permissions: userPermissions,
      });

      $scope.serverUsers = _.cloneDeep(thaUsers);
      $scope.users = _.cloneDeep(thaUsers);
      // $scope.users = _.cloneDeep($scope.serverUsers);
      $scope.currentUser = $scope.users[0];
    }
  }

  function loadUsers() {
    UserService.getUsers().then(handleUsersResponse);
  }

  function loadAll() {
    $q.all({
      roles: RoleService.getRoles(),
      users: UserService.getUsers(),
      permissions: PermissionService.getPermissions(),
    })
    .then(responses => {
      $scope.rawPermissions = responses.permissions.data;

      $scope.permissions = _.groupBy(responses.permissions.data, value => {
        return value.split('-').slice(0, 2).join('-');
      });

      $scope.rawRoles = responses.roles.data;
      $scope.roleNames = _.map($scope.rawRoles, "name");

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
