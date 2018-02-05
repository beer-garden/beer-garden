
commandService.$inject = ['$http', '$rootScope', 'SystemService'];
export default function commandService($http, $rootScope, SystemService) {
  var CommandService = {};

  CommandService.getSystemName = function(command) {
    var system = CommandService.findSystem(command);
    return system.display_name || system.name;
  }

  CommandService.findSystem = function(command) {
    var system_id = command.system.id;
    for( var index in $rootScope.systems ) {
      if ( system_id == $rootScope.systems[index].id ) {
        return $rootScope.systems[index];
      }
    }
  }

  CommandService.getCommands = function() {
    return $http.get('api/v1/commands');
  }

  CommandService.getCommand = function(id) {
    return $http.get('api/v1/commands/' + id);
  }

  CommandService.comparison = function(a, b) {
    var aSystem = CommandService.getSystemName(a);
    var bSystem = CommandService.getSystemName(b);

    if(aSystem < bSystem) return -1;
    if(aSystem > bSystem) return 1;
    if(a.name < b.name) return -1;
    if(a.name > b.name) return 1;
    return 0;
  };

  return CommandService;
};
