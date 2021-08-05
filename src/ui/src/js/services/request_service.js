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

  let service = {
    getRequests: (data) => {
      return $http.get(
        'api/v1/requests', {params: data}
      );
    },
    getRequest: (id) => {
      return $http.get('api/v1/requests/' + id);
    },
    isComplete: (request) => {
      return _.includes(completeStatuses, request.status);
    },
  };

  _.assign(service, {
    createRequest: (request, waitForCompletion) => {
      let promise = $http.post('api/v1/requests', request);

      if(!waitForCompletion) {
        return promise;
      }

      let deferred = $q.defer();
      promise.then(
        (response) => {
          let maxTries = 60;
          let curTry = 0;

          let inter = $interval(() => {
            service.getRequest(response.data.id).then(
              (response) => {
                if(service.isComplete(response.data)) {
                  deferred.resolve(response.data);
                  $interval.cancel(inter);
                }

                if(curTry++ >= maxTries) {
                  deferred.reject("Timeout expired");
                  $interval.cancel(inter);
                }
              },
              (errorResponse) => {
                deferred.reject(errorResponse.data);
                $interval.cancel(inter);
              }
            );
          }, 500);
        },
        (errorResponse) => {
          deferred.reject(errorResponse.data);
        }
      );

      return deferred.promise;
    },
  });

  return service;
};
