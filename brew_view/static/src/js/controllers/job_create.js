jobCreateController.$inject = [
  '$scope',
  '$rootScope',
  '$location',
  '$interval',
  '$stateParams',
  'JobService',
  'SystemService',
  'UtilityService',
  'SFBuilderService',
];

/**
 * jobCreateController - Controller for the job create page.
 * @param  {$scope} $scope         Angular's $scope object.
 * @param  {$rootScope} $rootScope Angular's $rootScope object.
 * @param  {$location} $location   Angular's $location object.
 * @param  {$interval} $interval   Angular's $interval object.
 * @param  {$stateParams} $stateParams Angular's $stateParams object.
 * @param  {Object} JobService Beer-Garden's job service.
 * @param  {Object} SystemService Beer-Garden's system service.
 * @param  {Object} UtilityService Beer-Garden's utility service service.
 * @param  {Object} SFBuilderService Beer-Garden's schema-form service.
 */
export default function jobCreateController(
  $scope,
  $rootScope,
  $location,
  $interval,
  $stateParams,
  JobService,
  SystemService,
  UtilityService,
  SFBuilderService) {
    $scope.systems = {
      data: [],
      loaded: false,
      error: false,
      errorMessage: '',
      status: null,
      errorMap: {
        'empty': {
          'solutions': [
            {
              problem: 'Backend Down',
              description: 'If the backend is down, there will be no systems to control',
              resolution: '<kbd>service bartender start</kbd>',
            },
            {
              problem: 'Plugin Problems',
              description: 'If Plugins attempted to start, but are failing to startup, then ' +
                          'you\'ll have to contact the plugin maintainer. You can tell what\'s ' +
                          ' wrong by their logs. Plugins are located at ' +
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
              problem: 'There Are No Systems',
              description: 'If no one has ever developed any plugins, then there will be no ' +
                          'systems here. You\'ll need to build your own plugins.',
              resolution: 'Develop a Plugin',
            },
          ],
        },
      },
    };
    $scope.system = $stateParams.system || null;
    $scope.command = $stateParams.command || null;
    $scope.instanceName = null;
    $scope.requestTemplate = null;
    $scope.jobAlerts = [];
    $scope.requestAlerts = [];
    $scope.job = null;
    $scope.jsonValues = {
      'requestModel': '',
      'jobModel': '',
    };
    $scope.requestSchema = null;
    $scope.requestForm = null;
    $scope.requestModel = $stateParams.request || {};

    $scope.jobSchema = null;
    $scope.jobForm = null;
    $scope.jobModel = {};


    $scope.successCallback = function(response) {
      $scope.systems.data = response.data;
      $scope.systems.loaded = true;
      $scope.systems.error = false;
      $scope.systems.status = response.status;
      $scope.systems.errorMessage = '';
    };

    $scope.failureCallback = function(response) {
      $scope.systems.data = [];
      $scope.systems.loaded = false;
      $scope.systems.error = true;
      $scope.systems.status = response.status;
      $scope.systems.errorMessage = response.data.message;
    };

    $scope.exploreSystem = function(system) {
      $location.path($rootScope.getSystemUrl(system.id));
    };

    $scope.selectCommand = function(command) {
      $scope.command = command;
      generateRequestSF();
    };

    $scope.selectSystem = function(system) {
      $scope.system = system;
    };

    $scope.resetRequest = function(form, model, system, command) {
      $scope.requestAlerts.splice(0);
      $scope.requestModel = {};

      generateRequestSF();
      form.$setPristine();
    };

    $scope.resetJob = function(form, model, system, command) {
      $scope.jobAlerts.splice(0);
      $scope.jobModel = {};

      generateJobSF();
      form.$setPristine();
    };

    $scope.closeJobAlert = function(index) {
      $scope.jobAlerts.splice(index, 1);
    };

    $scope.closeRequestAlert = function(index) {
      $scope.requestAlerts.splice(index, 1);
    };

    $scope.loadPreview = function(_editor) {
      UtilityService.formatJsonDisplay(_editor, true);
    };

    let generateJobSF = function() {
      $scope.jobSchema = JobService.SCHEMA;
      $scope.jobForm = JobService.FORM;
      $scope.$broadcast('schemaFormRedraw');
    };


    const extraValidate = function(model) {
      let triggerType = model['trigger_type'];
      let valid = true;
      if (!angular.isDefined(triggerType) || triggerType === null) {
        return false;
      }

      for (let key of JobService.getRequiredKeys(triggerType)) {
        if (!angular.isDefined(model[key]) || model[key] === null) {
          $scope.jobAlerts.push('Missing required key: ' + key);
          valid = false;
        }
      }

      if (triggerType === 'interval') {
        if (
          (
            (
              angular.isDefined(model['interval_start_date']) &&
              model['interval_start_date'] !== null
            ) ||
            (
              angular.isDefined(model['interval_end_date']) &&
              model['interval_end_date'] !== null
            )
          ) &&
          (
            !angular.isDefined(model['interval_timezone']) ||
            model['interval_timezone'] === null
          )
        ) {
          $scope.jobAlerts.push('If a date is specified, you must specify the timezone.');
          valid = false;
        }
      }

      if (triggerType === 'cron') {
        if (
          (
            (
              angular.isDefined(model['cron_start_date']) &&
              model['cron_start_date'] !== null
            ) ||
            (
              angular.isDefined(model['cron_end_date']) &&
              model['cron_end_date'] !== null
            )
          ) &&
          (
            !angular.isDefined(model['cron_timezone']) ||
            model['cron_timezone'] === null
          )
        ) {
          $scope.jobAlerts.push('If a date is specified, you must specify the timezone.');
          valid = false;
        }
      }

      return valid;
    };

    $scope.submitJobForm = function(form, model) {
      $scope.jobAlerts.splice(0);

      $scope.$broadcast('schemaFormValidate');

      let valid = extraValidate(model);

      if (form.$valid && valid) {
        let serverModel = JobService.formToServerModel(model, $scope.requestTemplate);
        JobService.createJob(serverModel).then(
          function(response) {
            $location.path('/jobs/' + response.data.id);
          },
          function(response) {
            $scope.createError = true;
            $scope.createErrorMessage = response.data.message;
          }
        );
      } else {
        $scope.jobAlerts.push('Looks like there was an error validating the request.');
      }
    };

    let generateRequestSF = function() {
      let sf = SFBuilderService.build($scope.system, $scope.command);
      $scope.requestSchema = sf['schema'];
      $scope.requestForm = sf['form'];
      $scope.$broadcast('schemaFormRedraw');
    };

    $scope.$watch('jobModel', function(val, old) {
      if (val && val !== old) {
        try {
          $scope.jsonValues.jobModel = angular.toJson(val, 2);
        } catch (e) {
          console.error('Error attempting to stringify the model');
        }
      }
    }, true);

    $scope.$watch('requestModel', function(val, old) {
      if (val && val !== old) {
        if ($scope.system['display_name']) {
          val['system'] = $scope.system['display_name'];
        }

        try {
          $scope.jsonValues.requestModel = angular.toJson(val, 2);
        } catch (e) {
          console.error('Error attempting to stringify the model');
        }
      }
    }, true);

    $scope.submitRequestForm = function(form, model) {
      // Remove all the old alerts so they don't just stack up
      $scope.requestAlerts.splice(0);

      // Give all the fields the chance to validate
      $scope.$broadcast('schemaFormValidate');

      // This is gross, but tv4 does not handle arrays well and throws errors
      // where it shouldn't. I don't think it's possible to fix without a patch
      // to tv4 or ASF so for now just ignore the false positive.
      let valid = true;
      if (!form.$valid) {
        angular.forEach(form.$error, function(errorGroup, errorKey) {
          if (errorKey !== 'schemaForm') {
            angular.forEach(errorGroup, function(error) {
              if (errorKey !== 'tv4-0' || !Array.isArray(error.$modelValue)) {
                valid = false;
              }
            });
          }
        });
      }

      if (valid) {
        let newRequest = angular.copy($scope.requestModel);

        if (
          $scope.system['display_name'] &&
          $scope.system['display_name'] === newRequest['system']
        ) {
          newRequest['system'] = $scope.system['name'];
          newRequest['metadata'] = {'system_display_name': $scope.system['display_name']};
        }
        generateJobSF();
        $scope.requestTemplate = newRequest;
      } else {
        $scope.requestAlerts.push('Looks like there was an error validating the request.');
      }
    };

    if ($stateParams.request) {
      generateRequestSF();
      $scope.jsonValues.requestModel = angular.toJson($stateParams.request, 2);
    } else {
      SystemService.getSystems().then($scope.successCallback, $scope.failureCallback);
    }
};
