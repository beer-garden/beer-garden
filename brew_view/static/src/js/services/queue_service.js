
queueService.$inject = ['$http'];

/**
 * queueService - Service for intereacting with the QueueAPI
 * @param  {$http} $http Angular's $http Object.
 * @return {Object}      Service for intereacting with the QueueAPI
 */
export default function queueService($http) {
  return {
    getQueues: function(success, error) {
      return $http.get('api/v1/queues');
    },
    clearQueues: function() {
      return $http.delete('api/v1/queues');
    },
    clearQueue: function(name) {
      return $http.delete('api/v1/queues/' + name);
    },
  };
};
