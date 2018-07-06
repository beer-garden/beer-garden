
commandService.$inject = ['$http', '$rootScope'];

/**
 * commandService - Service for interacting with the command API.
 * @param  {$http} $http           Angular's $http Object.
 * @param  {$rootScope} $rootScope Angular's $rootScope Object.
 * @return {Object}               Service for interacting with the command API.
 */
export default function commandService($http, $rootScope) {
  return {
    getCommands: function() {
      return $http.get('api/v1/commands');
    },
    getCommand: function(id) {
      return $http.get('api/v1/commands/' + id);
    },
    findSystem: function(command) {
      return $rootScope.findSystemByID(command.system.id);
    },
    getStateParams: function(command) {
      let system = $rootScope.findSystemByID(command.system.id);
      return {
        systemName: system.name,
        systemVersion: $rootScope.getVersionForUrl(command.system),
        name: command.name,
        id: command.id,
      };
    },
  };
};
