
systemService.$inject = ['$http'];


/**
 * systemService - Service for getting systems from the API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}      Object for interacting with the system API.
 */
export default function systemService($http) {
  let SystemService = {};

  SystemService.startSystem = function(system) {
    return $http.patch('api/v1/instances/' + system.instances[0].id,
      {operations: [{operation: 'replace', path: '/status', value: 'starting'}]}
    );
  };

  SystemService.stopSystem = function(system) {
    return $http.patch('api/v1/instances/' + system.instances[0].id,
      {operations: [{operation: 'replace', path: '/status', value: 'stopping'}]}
    );
  };

  SystemService.reloadSystem = function(system) {
    return $http.patch('api/v1/systems/' + system.id,
      {operations: [{operation: 'reload', path: '', value: ''}]}
    );
  };

  SystemService.deleteSystem = function(system) {
    return $http.delete('api/v1/systems/' + system.id);
  };

  SystemService.getSystems = function(dereference_nested, includeFields,
      excludeFields) {
    return $http.get('api/v1/systems', {
      params: {
        dereference_nested: dereference_nested,
        include_fields: includeFields,
        exclude_fields: excludeFields,
      }
    });
  };

  SystemService.getSystem = function(id, includeCommands) {
    return $http.get('api/v1/systems/' + id, {
      params: {include_commands: includeCommands}
    });
  };

  SystemService.getSystemID = function(request) {
    const promise = $http.get('api/v1/systems',
      {params: {name: request.system, include_commands: true}})
      .then(function(response) {
        let systemId = null;
        if (response.data.length > 0) {
          for (let i = 0; i < response.data[0].commands.length; i++) {
            let command = response.data[0].commands[i];
            if (command.name === request.command) {
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
