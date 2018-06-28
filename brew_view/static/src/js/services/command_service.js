
commandService.$inject = ['$http', '$rootScope', 'SystemService'];

/**
 * commandService - Service for interacting with the command API.
 * @param  {$http} $http           Angular's $http Object.
 * @param  {$rootScope} $rootScope Angular's $rootScope Object.
 * @param  {Object} SystemService  Service for interacting with the system API.
 * @return {Object}               Service for interacting with the command API.
 */
export default function commandService($http, $rootScope, SystemService) {
  return {
    getCommands: function() {
      return $http.get('api/v1/commands');
    },
    getCommand: function(id) {
      return $http.get('api/v1/commands/' + id);
    },
  };
};
