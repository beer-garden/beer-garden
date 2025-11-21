queueService.$inject = ['$http'];

/**
 * queueService - Service for intereacting with the QueueAPI
 * @param  {$http} $http Angular's $http Object.
 * @return {Object}      Service for intereacting with the QueueAPI
 */
export default function queueService($http) {
  return {
    getQueues: (success, error) => {
      return $http.get('api/v1/queues');
    },
    clearQueues: (gardenName) => {
      if (gardenName) {
        return $http.delete(
          'api/v1/queues?garden_name=' + encodeURIComponent(gardenName),
          {headers: {'Target-Garden': gardenName}}
        );
      } else {
        return $http.delete('api/v1/queues');
      }
    },
    clearQueue: (name) => {
      return $http.delete('api/v1/queues/' + name);
    },
    getInstanceQueues: (instanceId) => {
      return $http.get('api/v1/instances/' + instanceId + '/queues');
    },
  };
}
