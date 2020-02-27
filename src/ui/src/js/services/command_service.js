
commandService.$inject = ['$http', '$rootScope'];

/**
 * commandService - Service for interacting with the command API.
 * @param  {$http} $http           Angular's $http Object.
 * @param  {$rootScope} $rootScope Angular's $rootScope Object.
 * @return {Object}               Service for interacting with the command API.
 */
export default function commandService($http, $rootScope, SystemService) {
  return {
    getCommands: (params) => {
      return $http.get('api/v1/commands', {params: params});
    },
    getCommand: (id) => {
      return $http.get('api/v1/commands/' + id);
    },
    // findSystem: (command) => {
    //   return $rootScope.findSystemByID(command.system.id);
    // },
    getStateParams: (command) => {
      let system = SystemService.findSystemByID(command.system.id);
      return {
        systemName: system.name,
        // systemVersion: $rootScope.getVersionForUrl(command.system),
        systemVersion: system.version,
        commandName: command.name,
      };
    },
  };
};
