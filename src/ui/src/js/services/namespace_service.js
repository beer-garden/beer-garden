
namespaceService.$inject = ['$stateParams'];


/**
 * namespaceService - Service for getting namespaces from the API.
 * @param  {Object} $stateParams  Angular's $stateParams object.
 * @return {Object}               Object for interacting with the namespace API.
 */
export default function namespaceService($stateParams) {
  return {
    current: () => {
      return $stateParams.namespace;
    },
    default: (namespace) => {
      return namespace || $stateParams.namespace;
    },
  };
};
