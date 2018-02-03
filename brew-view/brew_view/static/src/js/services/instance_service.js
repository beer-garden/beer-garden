
instanceService.$inject = ['$http'];
export default function instanceService($http) {
  return {
    startInstance: function(instance) {
      return $http.patch('api/v1/instances/' + instance.id,
        {operations: [{operation: 'replace', path: '/status', value: 'starting'}]}
      );
    },
    stopInstance: function(instance) {
      return $http.patch('api/v1/instances/' + instance.id,
        {operations: [{operation: 'replace', path: '/status', value: 'stopping'}]}
      );
    }
  };
};
