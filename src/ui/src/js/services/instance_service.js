
instanceService.$inject = ['$http'];

/**
 * instanceService - Service for interacting with the instance API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}      Service for interacting with the instance API.
 */
export default function instanceService($http) {
  return {
    startInstance: (instance) => {
      return $http.patch('api/v1/instances/' + instance.id, {operation: 'start'});
    },
    stopInstance: (instance) => {
      return $http.patch('api/v1/instances/' + instance.id, {operation: 'stop'});
    },
    getInstance: (instanceId) => {
        return $http.get('api/v1/instances/' + instanceId)
    },
    getInstanceLogs: (instanceId, wait_timeout, start_line, end_line) => {
      return $http.patch('api/v1/instances/' + instanceId, {
        operation: 'logs',
        value: {
          "start_line":start_line,
          "end_line":end_line,
          "wait_timeout": wait_timeout
        }
      });
    },
  };
};
