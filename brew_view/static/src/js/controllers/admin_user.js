import _ from 'lodash';

adminUserController.$inject = [
  '$scope',
  '$q',
  'RoleService',
  'UserService',
  'PermissionService',
];

/**
 * adminUserController - System management controller.
 * @param  {$scope} $scope            Angular's $scope object.
 * @param  {$scope} $q                Angular's $q object.
 * @param  {Object} RoleService       Beer-Garden's role service object.
 * @param  {Object} UserService       Beer-Garden's user service object.
 * @param  {Object} PermissionService Beer-Garden's permission service object.
 */
export default function adminUserController(
    $scope,
    $q,
    RoleService,
    UserService,
    PermissionService) {
  $scope.users = [];
  $scope.serverUsers = [];
  $scope.showModify = true;

  $scope.doCreate = (create) => {
    if (create.password === create.verify) {
      UserService.createUser(create.username, create.password);
    }
  };

  $scope.doUpdate = () => {
    let newRoles = _.transform(
      $scope.currentUser.roles,
      (result, n, key, obj) => {
        if (n) {
          result.push(key);
        }
      },
      []
    );
    UserService.setRoles($scope.currentUser.id, newRoles).then(loadUsers);
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

  function handleUsersResponse(response) {
    $scope.rawUsers = response.data;
    $scope.users = [];

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

      $scope.serverUsers.push({
        id: user.id,
        username: user.username,
        roles: userRoles,
        permissions: userPermissions,
      });

      $scope.users = _.cloneDeep($scope.serverUsers);
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

      $scope.roles = responses.roles.data;
      $scope.roleNames = _.map($scope.roles, "name");

      handleUsersResponse(responses.users);
    });
  };

  loadAll();
};
