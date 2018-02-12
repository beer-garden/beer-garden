
queueService.$inject = ['$http'];

/**
 * queueService - Service for intereacting with the QueueAPI
 * @param  {$http} $http Angular's $http Object.
 * @return {Object}      Service for intereacting with the QueueAPI
 */
export default function queueService($http) {
  return {
    errorMap: {
      'empty': {
        'solutions': [
          {
            problem: 'Backend Down',
            description: 'If the backend is down, there will be no queues to control',
            resolution: '<kbd>service bartender start</kbd>',
          },
          {
            problem: 'Plugin Problems',
            description: 'If Plugins attempted to start, but are failing to startup, then' +
                          'you\'ll have to contact the plugin maintainer. You can tell what\'s '+
                          'wrong by their logs. Plugins are located at ' +
                          '<code>$APP_HOME/plugins</code>',
            resolution: '<kbd>less $APP_HOME/log/my-plugin.log</kbd>',
          },
          {
            problem: 'Database Names Do Not Match',
            description: 'It is possible that the backend is pointing to a Different Database ' +
                         'than the Frontend. Check to make sure that the <code>DB_NAME</code> ' +
                         'in both config files is the same',
            resolution: '<kbd>vim $APP_HOME/conf/bartender.json</kbd><br />' +
                          '<kbd>vim $APP_HOME/conf/brew-view.json</kbd>',
          },
          {
            problem: 'There Are No Queues',
            description: 'If no one has ever developed any plugins, then there will be no queues' +
                         'here. You\'ll need to build your own plugins.',
            resolution: 'Develop a Plugin',
          },
        ],
      },
    },

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
