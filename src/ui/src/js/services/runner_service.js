
runnerService.$inject = ['$http'];

/**
 * runnerService - Service for interacting with the runner API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}
 */
export default function runnerService($http) {
  return {
    getRunner: (runnerId) => {
      return $http.get('api/vbeta/runners/' + runnerId);
    },
    getRunners: () => {
      return $http.get('api/vbeta/runners/');
    },
    removeRunner: (runnerId) => {
      return $http.delete('api/vbeta/runners/' + runnerId);
    },
  };
};
