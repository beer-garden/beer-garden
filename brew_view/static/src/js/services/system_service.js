
systemService.$inject = ['$http'];


/**
 * systemService - Service for getting systems from the API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}      Object for interacting with the system API.
 */
export default function systemService($http) {
  return {
    getSystem: (id, includeCommands) => {
      return $http.get('api/v1/systems/' + id,
        {params: {include_commands: includeCommands}}
      );
    },
    getSystems: (dereferenceNested, includeFields, excludeFields) => {
      return $http.get('api/v1/systems', {
        params: {
          dereference_nested: dereferenceNested,
          include_fields: includeFields,
          exclude_fields: excludeFields,
        },
      });
    },
    deleteSystem: (system) => {
      return $http.delete('api/v1/systems/' + system.id);
    },
    reloadSystem: (system) => {
      return $http.patch('api/v1/systems/' + system.id,
        {operation: 'reload', path: '', value: ''}
      );
    },
  };
};
