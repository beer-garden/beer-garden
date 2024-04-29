addRemoveRolesController.$inject = ['$scope', '$uibModalInstance', 'UserService', 'RoleService'];

/**
 * addRemoveRolesController - Controller for change user roles modal.
 * @param  {Object} $scope             Angular's $scope object.
 * @param  {$scope} $uibModalInstance  Angular UI's $uibModalInstance object.
 * @param  {Object} UserService        Beer-Garden's user service.
 * @param  {Object} RoleService        Beer-Garden's role service.
 * @param  {Object} User               User model to modify
 */
export default function addRemoveRolesController($scope, $uibModalInstance, UserService, RoleService, user) {
    $scope.cancel = function() {
        $uibModalInstance.close();
      };
    
    $scope.user = user;
    $scope.user_roles = [...user.local_roles];

    $scope.selectAllValue = false;

    $scope.selectAll = function() {
    const filteredData = $scope.dtInstance.DataTable.rows( {search: 'applied'} ).data();
    
    $scope.selectAllValue = !$scope.selectAllValue;
        for (let i = 0; i < filteredData.length; i++) {
            const role = $scope.data.find((item) => item.name === filteredData[i][1]);
            if ($scope.selectAllValue && !$scope.user_roles.includes(role.name)){
                $scope.user_roles.push(role.name)
            } else if (!$scope.selectAllValue && $scope.user_roles.includes(role.name)) {
                $scope.user_roles = $scope.user_roles.splice($scope.user_roles.indexOf(role.name), 1);
            }
        }
    };

    $scope.cancelSubmission = function() {
        $scope.user_roles = [...user.local_roles];
    }

    $scope.submitRoles = function() {
        $scope.user.local_roles = $scope.user_roles;

        UserService.updateUser($scope.user.username, $scope.user);
    }

    $scope.data = RoleService.getRoles().then(
        (responses) => {
            $scope.data = responses.roles;
        },
        (response) => {
            $scope.response = response;
        },
    )


}