
adminService.$inject = ['$http'];
export default function adminService($http) {
  return {
    rescan: function() {
      return $http.patch('api/v1/admin/', {operations: [{operation: 'rescan'}]});
    }
  }
};
