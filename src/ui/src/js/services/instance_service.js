instanceService.$inject = ['$http'];

/**
 * instanceService - Service for interacting with the instance API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}      Service for interacting with the instance API.
 */
export default function instanceService($http) {
  return {
    startInstance: (instance, system) => {
      return $http.patch('api/v1/instances/' + instance.id, {
        operation: 'start',
      },{
        headers: {'Target-Garden': encodeURI(system.garden_name) == system.garden_name ? system.garden_name : undefined},
      });
    },
    stopInstance: (instance, system) => {
      return $http.patch('api/v1/instances/' + instance.id, {
        operation: 'stop',
      },{
        headers: {'Target-Garden': encodeURI(system.garden_name) == system.garden_name ? system.garden_name : undefined},
      });
    },
    getInstance: (instanceId) => {
      return $http.get('api/v1/instances/' + instanceId);
    },
    getInstanceLogs: (instanceId, timeout, startLine, endLine) => {
      return $http.get('api/v1/instances/' + instanceId + '/logs/', {
        params: {
          start_line: startLine,
          end_line: endLine,
          timeout: timeout,
        },
      });
    },
  };
}
