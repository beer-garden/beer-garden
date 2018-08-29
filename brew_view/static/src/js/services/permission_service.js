permissionService.$inject = ['$http'];

/**
 * roleService - Service for interacting with the role API.
 * @param  {$http} $http Angular's $http Object.
 * @return {Object}      Service for interacting with the permission API.
 */
export default function permissionService($http) {
  return {
    getPermissions: () => {
      return $http.get('api/v1/permissions/');
    },
  };
};
