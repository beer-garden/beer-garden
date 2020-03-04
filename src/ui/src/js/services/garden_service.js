
gardenService.$inject = ['$http'];

/**
 * gardenService - Service for interacting with the garden API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}      Service for interacting with the garden API.
 */
export default function gardenService($http) {
  return {
    getGardens: () => {
      return $http.get('api/v1/gardens/');
    },
    getGarden: (garden) => {
      return $http.get('api/v1/gardens/' + garden.name);
    },
    createGarden: (garden) => {
      return $http.post('api/v1/gardens', garden);
    },
    deleteGarden: (garden) => {
      return $http.delete('api/v1/gardens/' + garden.name);
    },
  };
};
