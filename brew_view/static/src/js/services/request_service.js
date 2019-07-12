import _ from 'lodash';

requestService.$inject = ['$q', '$http', '$timeout', 'NamespaceService'];

/**
 * requestService - Service for accessing the Request API.
 * @param  {Object} $q                Angular's $q object.
 * @param  {Object} $http             Angular's $http object.
 * @param  {Object} $timeout          Angular's $timeout object.
 * @param  {Object} NamespaceService  Beer-Garden's namespace service.
 * @return {Object}                   An Object for interacting with the Request API.
 */
export default function requestService($q, $http, $timeout, NamespaceService) {
  const completeStatuses = ['SUCCESS', 'ERROR', 'CANCELED'];

  let service = {
    getRequests: (data, options = {}) => {
      let namespace = NamespaceService.default(options.namespace);
      return $http.get(
        'api/v2/namespaces/'+namespace+'/requests', {params: data}
      );
    },
    getRequest: (id, options = {}) => {
      let namespace = NamespaceService.default(options.namespace);
      return $http.get('api/v2/namespaces/'+namespace+'/requests/' + id);
    },
    createRequest: (request, options = {}) => {
      let namespace = NamespaceService.default(options.namespace);
      return $http.post('api/v2/namespaces/'+namespace+'/requests', request);
    },
    isComplete: (request) => {
      return _.includes(completeStatuses, request.status);
    },
  };

  _.assign(service, {
    createRequestWait: (request, options = {}) => {
      let deferred = $q.defer();

      const checkForCompletion = function(id) {
        service.getRequest(id, options).then(
          (response) => {
            if (!service.isComplete(response.data)) {
              $timeout(() => {
                checkForCompletion(id);
              }, 500);
            } else {
              response.data = JSON.parse(response.data.output);
              deferred.resolve(response);
            }
        });
      };

      service.createRequest(request, options).then(
        (response) => {
          checkForCompletion(response.data.id);
        }
      );

      return deferred.promise;
    },
  });

  return service;
};
