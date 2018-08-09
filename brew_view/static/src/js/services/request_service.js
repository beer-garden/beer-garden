import _ from 'lodash';

requestService.$inject = ['$q', '$http', '$timeout'];

/**
 * requestService - Service for accessing the Request API.
 * @param  {$q} $q             Angular's $q object.
 * @param  {$http} $http       Angular's $http object.
 * @param  {$timeout} $timeout Angular's $timeout object.
 * @return {Object}            An Object for interacting with the Request API.
 */
export default function requestService($q, $http, $timeout) {
  const completeStatuses = ['SUCCESS', 'ERROR', 'CANCELED'];

  let service = {
    getRequests: (data) => {
      return $http.get('api/v1/requests', {params: data});
    },
    getRequest: (id) => {
      return $http.get('api/v1/requests/' + id);
    },
    createRequest: (request) => {
      return $http.post('api/v1/requests', request);
    },
    isComplete: (request) => {
      return _.includes(completeStatuses, request.status);
    },
  };

  _.assign(service, {
    createRequestWait: (request) => {
      let deferred = $q.defer();

      const checkForCompletion = function(id) {
        service.getRequest(id).then(
          (response) => {
            if (!service.isComplete(response.data)) {
              $timeout(() => { checkForCompletion(id) }, 500);
            } else {
              response.data = JSON.parse(response.data.output);
              deferred.resolve(response);
            }
        });
      };

      service.createRequest(request).then(
        (response) => {
          checkForCompletion(response.data.id);
        }
      );

      return deferred.promise;
    },
  });

  return service;
};
