
adminService.$inject = ['$http'];

/**
 * adminService - Service for interacting with the admin API.
 * @param  {$http} $http Angular's $http Object.
 * @return {Object}      Service for interacting with the admin API.
 */
export default function adminService($http) {
  return {
    rescan: function() {
      return $http.patch('api/v1/admin/', {operations: [{operation: 'rescan'}]});
    },
  };
};
