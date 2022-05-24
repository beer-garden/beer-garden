commandPublishingBlocklistService.$inject = ['$q', '$http'];

/**
 * @param  {Object} $q                Angular $q object.
 * @param  {Object} $http             Angular $http object.
 * @return {Object}                Service for interacting with the user API.
 */
export default function commandPublishingBlocklistService($q, $http) {
  return {
    getCommandPublishingBlocklist: () => {
      return $http.get('api/v1/commandpublishingblocklist');
    },
    deleteCommandPublishingBlocklist: (id) => {
      return $http.delete('api/v1/commandpublishingblocklist/' + id);
    },
    addToBlocklist: (blockedCommands) => {
      const requestBody = {'command_publishing_blocklist': blockedCommands};
      return $http.post('api/v1/commandpublishingblocklist', requestBody, {
        headers: {
          'Content-Type': 'application/json',
        },
      });
    },
  };
}
