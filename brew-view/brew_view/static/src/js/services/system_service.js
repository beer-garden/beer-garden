
systemService.$inject = ['$http'];
export default function systemService($http) {
  var SystemService = {};

  SystemService.startSystem = function(system) {
    return $http.patch('api/v1/instances/' + system.instances[0].id,
      {operations: [{operation: 'replace', path: '/status', value: 'starting'}]}
    );
  }

  SystemService.stopSystem = function(system) {
    return $http.patch('api/v1/instances/' + system.instances[0].id,
      {operations: [{operation: 'replace', path: '/status', value: 'stopping'}]}
    );
  }

  SystemService.reloadSystem = function(system) {
    return $http.patch('api/v1/systems/' + system.id,
      {operations: [{operation: 'reload', path: '', value: ''}]}
    );
  }

  SystemService.deleteSystem = function(system) {
    return $http.delete('api/v1/systems/' + system.id);
  }

  SystemService.getSystems = function() {
    return $http.get('api/v1/systems');
  }

  SystemService.getSystem = function(id, include_commands) {
    return $http.get('api/v1/systems/' + id, {params: {include_commands: include_commands}});
  }

  SystemService.getSystemID = function(request) {
    var promise = $http.get('api/v1/systems', {params: {name: request.system, include_commands: true} })
      .then(function(response) {
        var systemId = null;
        if(response.data.length > 0) {
          for(var i = 0; i < response.data[0].commands.length; i++) {
            var command = response.data[0].commands[i]
            if(command.name === request.command) {
              systemId = command.system.id;
              break;
            }
          }
        }
        return systemId;
      });
    return promise;
  };


  return SystemService;
};
