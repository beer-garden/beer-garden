
eventService.$inject = ['$websocket', 'TokenService'];

/**
 * eventService - Service for getting systems from the API.
 * @param  {$websocket} $websocket Angular's $websocket object.
 * @param  {TokenService} TokenService     Service for Token information.
 * @return {Object}      Object for interacting with the event API.
 */
export default function eventService($websocket, TokenService) {

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
        let proto = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        let eventUrl = proto + window.location.host + '/api/v1/socket/events';

        let token = TokenService.getToken();
        if (token) {
          eventUrl += '?token=' + token;
        }

        socketConnection = $websocket(eventUrl);

        socketConnection.onClose((message) => {
          console.log('Websocket closed: ' + message.reason);
        });
        socketConnection.onError((message) => {
          console.log('Websocket error: ' + message.reason);
        });
        socketConnection.onMessage((message) => {
          console.log(message);
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
