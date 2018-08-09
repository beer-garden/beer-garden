
instanceService.$inject = ['$http'];

/**
 * instanceService - Service for interacting with the instance API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}      Service for interacting with the instance API.
 */
export default function instanceService($http) {
  return {
    startInstance: function(instance) {
      return $http.patch('api/v1/instances/' + instance.id,
        {operation: 'replace', path: '/status', value: 'starting'}
      );
    },
    stopInstance: function(instance) {
      return $http.patch('api/v1/instances/' + instance.id,
        {operation: 'replace', path: '/status', value: 'stopping'}
      );
    },
  };
};
