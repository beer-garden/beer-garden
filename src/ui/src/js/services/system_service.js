systemService.$inject = ["$rootScope", "$http"];

/**
 * Compare two system versions. Intended to be used for sorting.
 *
 * Newer systems will be sorted to the front. For example, this would be the
 * result of sorting with this function:
 *
 * [ "1.1.0.dev0", "1.0.0", "1.0.0.dev1", "1.0.0.dev0", "1.0.0.dev" ]
 *
 * Note that versions with less parts are considered newer.
 *
 * @param {string} version1 - first version
 * @param {string} version2 - second version
 * @return {int} - result of comparison
 */
const compareVersions = function (version1, version2) {
  let parts1 = version1.split(".");
  let parts2 = version2.split(".");

  let numParts = Math.min(parts1.length, parts2.length);

  for (let i = 0; i < numParts; i++) {
    let intPart1 = parseInt(parts1[i]);
    let intPart2 = parseInt(parts2[i]);

    if (!isNaN(intPart1) && !isNaN(intPart2)) {
      if (intPart1 > intPart2) {
        return -1;
      } else if (intPart1 < intPart2) {
        return 1;
      }
    } else {
      if (parts1[i] > parts2[i]) {
        return -1;
      } else if (parts1[i] < parts2[i]) {
        return 1;
      }
    }
  }

  if (parts1.length < parts2.length) {
    return -1;
  } else if (parts1.length > parts2.length) {
    return 1;
  }

  return 0;
};

/**
 * systemService - Service for getting systems from the API.
 * @param  {$rootScope} $rootScope    Angular's $rootScope object.
 * @param  {Object} $http             Angular's $http object.
 * @return {Object}                   Object for interacting with the system API.
 */
export default function systemService($rootScope, $http) {
  let service = {
    getSystem: (id, options = {}) => {
      return $http.get("api/v1/systems/" + id, {
        params: { include_commands: options.includeCommands },
      });
    },
    getSystems: (options = {}, headers = {}) => {
      return $http.get("api/v1/systems", {
        params: {
          dereference_nested: options.dereferenceNested,
          include_fields: options.includeFields,
          exclude_fields: options.excludeFields,
          namespace: options.namespace,
        },
        headers: headers,
      });
    },
    deleteSystem: (system) => {
      return $http.delete("api/v1/systems/" + system.id);
    },
    forceDeleteSystem: (system) => {
      return $http.delete("api/v1/systems/" + system.id, {
        params: { force: true },
      });
    },
    reloadSystem: (system) => {
      return $http.patch("api/v1/systems/" + system.id, {
        operation: "reload",
        path: "",
        value: "",
      });
    },
  };

  /**
   * Converts a system's version to the 'latest' semantic url scheme.
   * @param {Object} system - system for which you want the version URL.
   * @return {string} - either the system's version or 'latest'.
   */
  service["getVersionForUrl"] = (system) => {
    // All versions for systems with the given system name
    let versions = _.map(
      _.filter($rootScope.systems, { name: system.name }),
      _.property("version")
    );

    // Sorted according to the system comparison function
    let sorted = versions.sort(compareVersions);

    return system.version == sorted[0] ? "latest" : system.version;
  };

  /**
   * Convert a system ObjectID to a route to use for the router.
   * @param {string} systemId  - ObjectID for system.
   * @return {string} url to use for UI routing.
   */
  service["getSystemUrl"] = (systemId) => {
    for (let system of $rootScope.systems) {
      if (system.id == systemId) {
        let version = service.getVersionForUrl(system);
        return "/systems/" + system.name + "/" + version;
      }
    }
    return "/systems";
  };

  /**
   * Find the system with the specified name/version (version can just
   * be the string 'latest')
   *
   * @param {string} name - The name of the system you wish to find.
   * @param {string} version - The version you want to find (or latest)
   * @return {Object} The latest system or undefined if it is not found.
   */
  service["findSystem"] = (namespace, name, version) => {
    let notFound = {
      data: { message: "No matching system" },
      errorGroup: "system",
      status: 404,
    };

    if (version !== "latest") {
      return _.find($rootScope.systems, {
        namespace: namespace,
        name: name,
        version: version,
      });
    }

    let filteredSystems = _.filter($rootScope.systems, {
      namespace: namespace,
      name: name,
    });
    if (_.isEmpty(filteredSystems)) {
      return undefined;
    }

    let versions = _.map(filteredSystems, _.property("version"));
    let sorted = versions.sort(compareVersions);

    return _.find(filteredSystems, { version: sorted[0] });
  };

  /**
   * Find the system with the given ID.
   * @param {string} systemId - System's ObjectID
   * @return {Object} the system with this ID.
   */
  service["findSystemByID"] = (systemId) => {
    for (let system of $rootScope.systems) {
      if (system.id === systemId) {
        return system;
      }
    }
  };

  return service;
}
