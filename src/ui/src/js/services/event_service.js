/**
 * eventService - Service for getting systems from the API.
 * @return {Object}                   Object for interacting with the event API.
 */
export default function eventService() {
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
    connect: () => {
      // If socket is already open don't do anything
      if (
        _.isUndefined(socketConnection) ||
        socketConnection.readyState == WebSocket.CLOSED
      ) {
        let eventUrl =
          (window.location.protocol === "https:" ? "wss://" : "ws://") +
          window.location.host +
          window.location.pathname +
          `api/v1/socket/events/`;

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
    updateToken: (token) => {
      if (socketConnection.readyState == WebSocket.OPEN) {
        socketConnection.send(
            JSON.stringify({name: "UPDATE_TOKEN", payload: token})
        );
      }
    },
  };
}
