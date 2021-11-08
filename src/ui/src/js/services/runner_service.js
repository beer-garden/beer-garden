runnerService.$inject = ["$http"];

/**
 * runnerService - Service for interacting with the runner API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}
 */
export default function runnerService($http) {
  return {
    getRunner: (runnerId) => {
      return $http.get("api/vbeta/runners/" + runnerId);
    },
    getRunners: () => {
      return $http.get("api/vbeta/runners/");
    },
    startRunner: (runner) => {
      return $http.patch("api/vbeta/runners/" + runner.id, {
        operation: "start",
      });
    },
    stopRunner: (runner) => {
      return $http.patch("api/vbeta/runners/" + runner.id, {
        operation: "stop",
      });
    },
    removeRunner: (runner) => {
      return $http.delete("api/vbeta/runners/" + runner.id);
    },
    reloadRunners: (path) => {
      return $http.patch("api/vbeta/runners/", {
        operation: "reload",
        path: path,
      });
    },
  };
}
