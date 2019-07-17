
systemService.$inject = ['$http'];


/**
 * systemService - Service for getting systems from the API.
 * @param  {Object} $http             Angular's $http object.
 * @return {Object}                   Object for interacting with the system API.
 */
export default function systemService($http) {
  return {
    getSystem: (id, options = {}) => {
      return $http.get('api/v1/systems/' + id,
        {params: {include_commands: options.includeCommands}}
      );
    },
    getSystems: (options = {}) => {
      return $http.get('api/v1/systems', {
        params: {
          dereference_nested: options.dereferenceNested,
          include_fields: options.includeFields,
          exclude_fields: options.excludeFields,
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
