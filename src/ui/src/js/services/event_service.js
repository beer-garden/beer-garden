
eventService.$inject = [
  'TokenService',
];

/**
 * eventService - Service for getting systems from the API.
 * @param  {Object} TokenService      Service for Token information.
 * @return {Object}                   Object for interacting with the event API.
 */
export default function eventService(TokenService) {

  let socketConnection = undefined;
  let messageCallbacks = {};

  let onMessage = (message) => {
    let event = JSON.parse(message.data);

    for (let callback of _.values(messageCallbacks)) {
      callback(event);
    }
  };

  return {
    addCallback: (name, callback) => {
      messageCallbacks[name] = callback;
    },
    removeCallback: (name) => {
      delete messageCallbacks[name];
    },
    connect: (token) => {
      // If socket is already open don't do anything
      if (_.isUndefined(socketConnection) || socketConnection.readyState == WebSocket.CLOSED) {
        let eventUrl = (window.location.protocol === 'https:' ? 'wss://' : 'ws://') +
          window.location.host +
          window.location.pathname +
          `api/v1/socket/events/`;

        if (token) {
          eventUrl += '?token=' + token;
        }

        socketConnection = new WebSocket(eventUrl);
        socketConnection.onmessage = onMessage;
      }
    },
    close: () => {
      if (!_.isUndefined(socketConnection)) {
        socketConnection.close();
      }
    },
    state: () => {
      if (socketConnection == undefined) {
        return undefined;
      }
      return socketConnection.readyState;
    },
  };
};
