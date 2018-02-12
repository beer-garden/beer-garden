
commandIndexController.$inject = [
  '$scope',
  'SystemService',
  'CommandService',
  'UtilityService',
  'DTOptionsBuilder',
];

/**
 * commandIndexController - Angular controller for all commands page.
 * @param  {$scope} $scope           Angular's $scope object.
 * @param  {Object} SystemService    Beer-Garden system service.
 * @param  {Object} CommandService   Beer-Garden command service.
 * @param  {Object} UtilityService   Beer-Garden utility service.
 * @param  {Object} DTOptionsBuilder Data-tables' builder for options.
 */
export default function commandIndexController(
  $scope,
  SystemService,
  CommandService,
  UtilityService,
  DTOptionsBuilder) {
  $scope.service = CommandService;
  $scope.util = UtilityService;

  $scope.commands = {
    data: [],
    loaded: false,
    status: null,
    error: false,
    errorMessage: '',
    errorMap: {
      'empty': {
        'solutions': [
          {
            problem: 'Backend Down',
            description: 'If the backend is down, there will be no commands to control',
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
            problem: 'There Are No Commands',
            description: 'If no one has ever developed any plugins, then there will be no ' +
                         'systems here. You\'ll need to build your own plugins.',
            resolution: 'Develop a Plugin',
          },
        ],
      },
    },
  };

  $scope.dtOptions = DTOptionsBuilder.newOptions()
    .withOption('order', [4, 'asc'])
    .withOption('autoWidth', false)
    .withBootstrap();

  $scope.successCallback = function(response) {
    // Make sure systems load before moving on with the sorting
    if ($scope.systems == null) {
      $scope.$on('systemsLoaded', function() {
        response.data.sort(CommandService.comparison);
      });
    } else {
      response.data.sort(CommandService.comparison);
    }

    $scope.commands.data = response.data;
    $scope.commands.loaded = true;
    $scope.commands.status = response.status;
    $scope.commands.error = false;
    $scope.commands.errorMessage = '';
  };

  $scope.failureCallback = function(response) {
    $scope.commands.data = [];
    $scope.commands.loaded = false;
    $scope.commands.error = true;
    $scope.commands.status = response.status;
    $scope.commands.errorMessage = response.data.message;
  };

  CommandService.getCommands().then($scope.successCallback, $scope.failureCallback);
};
