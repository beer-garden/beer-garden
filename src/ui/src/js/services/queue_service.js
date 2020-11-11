
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
    clearQueues: () => {
      return $http.delete('api/v1/queues');
    },
    clearQueue: (name) => {
      return $http.delete('api/v1/queues/' + name);
    },
    getInstanceQueues: (instance_id) => {
      return $http.get('api/v1/instances/' + instance_id + '/queues');
    },
  };
};
