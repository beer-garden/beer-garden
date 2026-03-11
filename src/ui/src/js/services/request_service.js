import _ from 'lodash';

requestService.$inject = ['$q', '$http', '$interval'];

/**
 * requestService - Service for accessing the Request API.
 * @param  {Object} $q                Angular $q object.
 * @param  {Object} $http             Angular $http object.
 * @param  {Object} $interval         Angular $interval object.
 * @return {Object}                   An Object for interacting with the Request API.
 */
export default function requestService($q, $http, $interval) {
  const completeStatuses = ['SUCCESS', 'ERROR', 'CANCELED', 'INVALID'];

  const service = {
    getRequests: (data) => {
      return $http.get('api/v1/requests', {params: data});
    },
    getRequest: (id) => {
      return $http.get('api/v1/requests/' + id);
    },
    isComplete: (request) => {
      return _.includes(completeStatuses, request.status);
    },
    deleteRequests: (data) => {
      return $http.delete('api/v1/requests', {params: data});
    },
    cancelRequest: (id) => {
      return $http.patch('api/v1/requests/' + id, {
        operation: 'replace',
        path: '/status',
        value: 'CANCELED',
      });
    },
    refreshRequest: (id) => {
      return $http.patch('api/v1/requests/' + id, {
        operation: 'rebroadcast',
      });
    },
  };

  _.assign(service, {
    createRequest: (request, waitForCompletion, isFormData) => {
      let promise = undefined;
      if (isFormData) {
        promise = $http.post('api/v1/requests?blocking=' + waitForCompletion, request, {
          headers: {
            'Content-Type': undefined,
            'Target-Garden': encodeURI(request.target_garden) == request.target_garden ? request.target_garden : undefined,
            'Source-Garden': encodeURI(request.source_garden) == request.source_garden ? request.source_garden : undefined,
          },
        });
      } else {
        promise = $http.post('api/v1/requests?blocking=' + waitForCompletion, request, {
          headers: {
            'Target-Garden': encodeURI(request.target_garden) == request.target_garden ? request.target_garden : undefined,
            'Source-Garden': encodeURI(request.source_garden) == request.source_garden ? request.source_garden : undefined,
          },
        });
      }

      if (!waitForCompletion) {
        return promise;
      }

      const deferred = $q.defer();
      promise.then(
          (response) => {
            if (service.isComplete(response.data)) {
              deferred.resolve(response.data);
            }
          },
          (errorResponse) => {
            deferred.reject(errorResponse.data);
          },
      );

      return deferred.promise;
    },
  });

  return service;
}
