
jobCreateSystemController.$inject = [ '$scope', '$rootScope' ];

/**
 * jobCreateController - Controller for the job create page.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $rootScope        Angular's $rootScope object.
 */
export default function jobCreateSystemController( $scope, $rootScope) {
  $scope.setWindowTitle('scheduler');

  $scope.response = $rootScope.sysResponse;

  $scope.data = [];

  for (let system of $rootScope.systems) {
        if ($rootScope.hasPermission($rootScope.user, 'CREATE', false, system.namespace)){
          $scope.data.push(system)
        }
      }
};