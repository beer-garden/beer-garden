
systemService.$inject = ['$http'];


/**
 * systemService - Service for getting systems from the API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}      Object for interacting with the system API.
 */
export default function systemService($http) {
  return {
    getSystem: (namespace, id, includeCommands) => {
      return $http.get('api/v2/namespaces/'+namespace+'/systems/' + id,
        {params: {include_commands: includeCommands}}
      );
    },
    getSystems: (namespace, dereferenceNested, includeFields, excludeFields) => {
      return $http.get('api/v2/namespaces/'+namespace+'/systems', {
        params: {
          dereference_nested: dereferenceNested,
          include_fields: includeFields,
          exclude_fields: excludeFields,
        },
      });
    },
    deleteSystem: (namespace, system) => {
      return $http.delete('api/v2/namespaces/'+namespace+'/systems/' + system.id);
    },
    reloadSystem: (namespace, system) => {
      return $http.patch('api/v2/namespaces/'+namespace+'/systems/' + system.id,
        {operation: 'reload', path: '', value: ''}
      );
    },
  };
};
