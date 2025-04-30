import {formatJsonDisplay} from '../../services/utility_service.js';

jobCreateRequestController.$inject = [
  '$scope',
  '$state',
  '$stateParams',
  '$q',
  'RequestService',
  'SFBuilderService',
  'SystemService',
];

/**
 * jobCreateRequestController - Controller for the job create page.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $state            Angular's $state object.
 * @param  {Object} $stateParams      Angular's $stateParams object.
 * @param  {Object} $q                Angular's $q object.
 * @param  {Object} RequestService    Beer-Garden's request service object.
 * @param  {Object} SFBuilderService  Beer-Garden's schema-form service.
 * @param  {Object} SystemService   Beer-Garden's system service object.
 */
export default function jobCreateRequestController(
    $scope,
    $state,
    $stateParams,
    $q,
    RequestService,
    SFBuilderService,
    SystemService,
) {
  $scope.setWindowTitle('scheduler');

  $scope.alerts = [];

  $scope.schema = null;
  $scope.form = null;
  $scope.model = {};
  $scope.job = null;

  if ($stateParams.job == null) {
    $scope.system = $stateParams.system;
    $scope.command = $stateParams.command;
  } else {
    $scope.system = SystemService.findSystem(
        $stateParams.job.request_template.namespace,
        $stateParams.job.request_template.system,
        $stateParams.job.request_template.system_version,
    );

    for (const i in $scope.system.commands) {
      if (
        $scope.system.commands[i].name ==
        $stateParams.job.request_template.command
      ) {
        $scope.command = $scope.system.commands[i];
        break;
      }
    }

    $scope.job = $stateParams.job;

    // Clone to allow resets
    $scope.model = _.cloneDeep($scope.job.request_template);
    $scope.modelJson = angular.toJson($scope.model, 2);
  }

  $scope.createRequestWrapper = function(requestPrototype, ...args) {
    const request = {
      command: requestPrototype['command'],
      command_display_name: requestPrototype['command_display_name'] || requestPrototype['command'],
      command_type: requestPrototype['command_type'] || 'TEMP',
      namespace: requestPrototype['namespace'] || $scope.system.namespace,
      system: requestPrototype['system'] || $scope.system.name,
      system_version:
        requestPrototype['system_version'] || $scope.system.version,
      instance_name:
        requestPrototype['instance_name'] || $scope.model['instance_name'],
    };

    // If a system has more than one instance this will be undefined on initial page
    // load. We could just let this continue as normal, but the backend would return
    // an error like "Could not find instance with name 'None' in system". That's not
    // the best, so this special handling makes the error message a little nicer.
    if (!request.instance_name) {
      const deferred = $q.defer();
      deferred.reject('Please select an instance');
      return deferred.promise;
    }

    // If parameters are specified we need to use the model value
    if (angular.isDefined(requestPrototype['parameterNames'])) {
      request['parameters'] = {};
      const nameList = requestPrototype['parameterNames'];
      for (let i = 0; i < nameList.length; i++) {
        request['parameters'][nameList[i]] = args[i];
      }
    }

    return RequestService.createRequest(request, true);
  };

  const generateRequestSF = function() {
    const sf = SFBuilderService.build($scope.system, $scope.command);

    $scope.schema = sf['schema'];
    $scope.form = sf['form'];

    $scope.$broadcast('schemaFormRedraw');
  };

  // These are shared with create_trigger
  $scope.loadPreview = function(_editor) {
    formatJsonDisplay(_editor, true);
  };
  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.$watch(
      'model',
      function(val, old) {
        if (val && val !== old) {
          if ($scope.system['display_name']) {
            val['system'] = $scope.system['display_name'];
          }

          try {
            $scope.modelJson = angular.toJson(val, 2);
          } catch (e) {
            console.error('Error attempting to stringify the model');
          }
        }
      },
      true,
  );

  $scope.submit = function(form, model) {
    // Remove all the old alerts so they don't just stack up
    $scope.alerts.splice(0);

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
      const newRequest = angular.copy($scope.model);

      if (
        $scope.system['display_name'] &&
        $scope.system['display_name'] === newRequest['system']
      ) {
        newRequest['system'] = $scope.system['name'];
        newRequest['metadata'] = {
          system_display_name: $scope.system['display_name'],
        };
      }

      $state.go('base.jobscreatetrigger', {
        job: $scope.job,
        request: newRequest,
      });
    } else {
      $scope.alerts.push(
          'Looks like there was an error validating the request.',
      );
    }
  };

  $scope.reset = function(form, model, system, command) {
    $scope.alerts.splice(0);

    if ($scope.job == null) {
      $scope.model = {};
    } else {
      $scope.model = _.cloneDeep($scope.job.request_template);
      $scope.modelJson = angular.toJson($scope.model, 2);
    }

    generateRequestSF();
    form.$setPristine();
  };

  generateRequestSF();
}
