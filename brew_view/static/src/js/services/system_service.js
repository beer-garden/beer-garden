
systemService.$inject = ['$http', 'NamespaceService'];


/**
 * systemService - Service for getting systems from the API.
 * @param  {Object} $http             Angular's $http object.
 * @param  {Object} NamespaceService  Beer-Garden's namespace service.
 * @return {Object}                   Object for interacting with the system API.
 */
export default function systemService($http, NamespaceService) {
  return {
    getSystem: (id, options = {}) => {
      let namespace = NamespaceService.default(options.namespace);

      return $http.get('api/v2/namespaces/'+namespace+'/systems/' + id,
        {params: {include_commands: options.includeCommands}}
      );
    },
    getSystems: (options = {}) => {
      let namespace = NamespaceService.default(options.namespace);

      return $http.get('api/v2/namespaces/'+namespace+'/systems', {
        params: {
          dereference_nested: options.dereferenceNested,
          include_fields: options.includeFields,
          exclude_fields: options.excludeFields,
        },
      });
    },
    deleteSystem: (system, options = {}) => {
      let namespace = NamespaceService.default(options.namespace);

      return $http.delete('api/v2/namespaces/'+namespace+'/systems/' + system.id);
    },
    reloadSystem: (system, options = {}) => {
      let namespace = NamespaceService.default(options.namespace);

      return $http.patch('api/v2/namespaces/'+namespace+'/systems/' + system.id,
        {operation: 'reload', path: '', value: ''}
      );
    },
  };
};
