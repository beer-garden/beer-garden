import _ from 'lodash';

requestService.$inject = ['$q', '$http', '$timeout'];

/**
 * requestService - Service for accessing the Request API.
 * @param  {Object} $q                Angular's $q object.
 * @param  {Object} $http             Angular's $http object.
 * @param  {Object} $timeout          Angular's $timeout object.
 * @return {Object}                   An Object for interacting with the Request API.
 */
export default function requestService($q, $http, $timeout) {
  const completeStatuses = ['SUCCESS', 'ERROR', 'CANCELED'];

  let service = {
    updateRequestExpiration: (request, expiration_date) => {
        return $http.patch(
            'api/v1/requests/' + request.id, {
                operation: 'replace',
                path: '/update_request_expiration',
                value: expiration_date,
            }
        )
    },
    getRequests: (data) => {
      return $http.get(
        'api/v1/requests', {params: data}
      );
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
