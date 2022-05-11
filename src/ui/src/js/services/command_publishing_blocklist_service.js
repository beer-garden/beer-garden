import _ from 'lodash';

commandPublishingBlocklistService.$inject = ['$q', '$http'];

/**
 * @param  {Object} $q                Angular $q object.
 * @param  {Object} $http             Angular $http object.
 * @return {Object}                Service for interacting with the user API.
 */
export default function commandPublishingBlocklistService($q, $http) {
  const service = {
    getCommandPublishingBlocklist: () => {
      return $http.get('api/v1/commandpublishingblocklist');
    },
    deleteCommandPublishingBlocklist: (id) => {
      const promise = $http.delete('api/v1/commandpublishingblocklist/' + id);
      const deferred = $q.defer();
      promise.then(
          (response) => {
            deferred.resolve(response);
          },
          (errorResponse) => {
            deferred.reject(errorResponse);
          },
      );

      return deferred.promise;
    },
  };

  _.assign(service, {
    addToBlocklist: (blockedCommands) => {
      const requestBody = {'command_publishing_blocklist': blockedCommands};
      const promise = $http.post('api/v1/commandpublishingblocklist', requestBody, {
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const deferred = $q.defer();
      promise.then(
          (response) => {
            deferred.resolve(response);
          },
          (errorResponse) => {
            deferred.reject(errorResponse);
          },
      );

      return deferred.promise;
    },
  });

  return service;
}
