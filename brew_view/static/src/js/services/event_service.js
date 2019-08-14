
eventService.$inject = ['$rootScope', '$websocket', 'TokenService'];

/**
 * eventService - Service for getting systems from the API.
 * @param  {Object} $rootScope        Angular's $rootScope object.
 * @param  {Object} $websocket        Angular's $websocket object.
 * @param  {Object} TokenService      Service for Token information.
 * @return {Object}                   Object for interacting with the event API.
 */
export default function eventService($rootScope, $websocket, TokenService) {

  let socketConnection = undefined;
  let messageCallback = undefined;

  return {
    setCallback: (callback) => {
      messageCallback = callback;
    },
    clearCallback: (callback) => {
      messageCallback = undefined;
    },
    connect: () => {
      if (window.WebSocket && !socketConnection) {
        let eventUrl = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
          window.location.host +
          window.location.pathname +
          `api/v2/namespaces/${$rootScope.getCurrentNamespace()}/events/socket`;

        let token = TokenService.getToken();
        if (token) {
          eventUrl += '?token=' + token;
        }

        socketConnection = $websocket(eventUrl);

        socketConnection.onClose((message) => {
        });
        socketConnection.onError((message) => {
          console.log('Websocket error: ' + message.reason);
        });
        socketConnection.onMessage((message) => {
          if (messageCallback) {
            messageCallback(message);
          }
        });
      }
    },
    close: () => {
      if (!_.isUndefined(socketConnection)) {
        socketConnection.close();
        socketConnection = undefined;
      }
    },
  };
};
