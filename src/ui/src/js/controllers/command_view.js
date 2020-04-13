import _ from 'lodash';
import angular from 'angular';
import {formatJsonDisplay} from '../services/utility_service.js';

commandViewController.$inject = [
  '$rootScope',
  '$scope',
  '$state',
  '$stateParams',
  '$sce',
  'RequestService',
  'SFBuilderService',
  'system',
  'command',
];

/**
 * commandViewController - Angular controller for a specific command.
 * @param  {Object} $rootScope        Angular's $rootScope object.
 * @param  {Object} $scope            Angular's $scope object.
 * @param  {Object} $state            Angular's $state object.
 * @param  {Object} $stateParams      Angular's $stateParams object.
 * @param  {Object} $sce              Angular's $sce object.
 * @param  {Object} RequestService    Beer-Garden's request service object.
 * @param  {Object} SFBuilderService  Beer-Garden's schema-form builder service object.
 */
export default function commandViewController(
    $rootScope,
    $scope,
    $state,
    $stateParams,
    $sce,
    RequestService,
    SFBuilderService,
    system,
    command) {

  let tempResponse = $rootScope.sysResponse;

  $scope.schema = {};
  $scope.form = [];
  $scope.model = $stateParams.request || {};
  $scope.alerts = [];
  $scope.baseModel = {};
  $scope.template = '';
  $scope.manualOverride = false;
  $scope.manualModel = '';

  $scope.system = system;

  $scope.jsonValues = {
    model: '',
    command: '',
    schema: '',
    form: '',
  };

  $scope.createRequestWrapper = function(requestPrototype, ...args) {
    let request = {
      command: requestPrototype['command'],
      namespace: requestPrototype['namespace'] || $scope.system.namespace,
      system: requestPrototype['system'] || $scope.system.name,
      system_version: requestPrototype['system_version'] || $scope.system.version,
      instance_name: requestPrototype['instance_name'] || $scope.model['instance_name'] ||
          'default',
    };

    // If parameters are specified we need to use the model value
    if (angular.isDefined(requestPrototype['parameterNames'])) {
      request['parameters'] = {};
      let nameList = requestPrototype['parameterNames'];
      for (let i=0; i<nameList.length; i++) {
        request['parameters'][nameList[i]] = args[i];
      };
    }

    return RequestService.createRequestWait(request).then(
      function(response) {
        return response.data;
      }
    );
  };

  $scope.checkInstance = function() {
    // Loops through all system instances to find status of the model.instance
    for (let i=0; i < $scope.system.instances.length; i++) {
        let instance = $scope.system.instances[i];

        // Checks status to show banner if not running, hide banner if running
        if (instance.name == $scope.model.instance_name) {
            if (instance.status != 'RUNNING') {
                return true;
            } else {
                return false;
            }
        }
    }
  };

  $scope.submitForm = function(form, model) {
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
      $scope.createRequest(model);
    } else {
      $scope.alerts.push('Looks like there was an error validating the request.');
    }
  };

  $scope.createRequest = function(request) {
    if (typeof(request) === 'string') {
      try {
        request = JSON.parse(request);
      } catch (err) {
        $scope.alerts.push(err);
        return;
      }
    }
    let newRequest = angular.copy(request);

    if ($scope.system['display_name'] &&
        $scope.system['display_name'] === newRequest['system']) {
      newRequest['system'] = $scope.system['name'];
      newRequest['metadata'] = {system_display_name: $scope.system['display_name']};
    }

    RequestService.createRequest(newRequest).then(
      function(response) {
        $state.go('base.request', {'requestId': response.data.id})
      },
      function(response) {
        $scope.createResponse = response;
      }
    );
  };

  $scope.reset = function(form, model, system, command) {
    $scope.createResponse = undefined;
    $scope.alerts.splice(0);
    $scope.model = {};

    generateSF();
    form.$setPristine();
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.loadPreview = function(_editor) {
    formatJsonDisplay(_editor, true);
  };

  $scope.loadEditor = function(_editor) {
    formatJsonDisplay(_editor, false);
  };

  $scope.toggleManualOverride = function() {
    $scope.alerts.splice(0);
    $scope.createResponse = undefined;
    $scope.manualOverride = !$scope.manualOverride;
    $scope.manualModel = $scope.jsonValues.model;
  };

  $scope.scheduleRequest = function() {
    $state.go('jobsCreate',
      {
        'request': $scope.model,
        'system': $scope.system,
        'command': $scope.command,
      }
    );
  };

  let generateSF = function() {
    let sf = SFBuilderService.build($scope.system, $scope.command);

    $scope.schema = sf['schema'];
    $scope.form = sf['form'];

    $scope.jsonValues.schema = JSON.stringify($scope.schema, undefined, 2);
    $scope.jsonValues.form = JSON.stringify($scope.form, undefined, 2);
  };

  $scope.successCallback = function(command) {
    $scope.command = command;
    $scope.jsonValues.command = JSON.stringify($scope.command, undefined, 2);

    // If this command has a custom template then we're done!
    if ($scope.command.template) {
      // This is necessary for things like scripts and forms
      if ($scope.config.allowUnsafeTemplates) {
        $scope.template = $sce.trustAsHtml($scope.command.template);
      } else {
        $scope.template = $scope.command.template;
      }

      $scope.response = $rootScope.sysResponse;
    } else {
      generateSF();
    }

    $scope.breadCrumbs = [
      $scope.system.namespace,
      $scope.system.display_name || $scope.system.name,
      $scope.system.version,
      $scope.command.name,
    ];

    $scope.setWindowTitle(
      $scope.command.name,
      ($scope.system.display_name || $scope.system.name),
      $scope.system.version,
      'command'
    );
  };

  $scope.failureCallback = function(response) {
    tempResponse = response;
    $scope.response = response;
    $scope.command = [];
    $scope.setWindowTitle();
  };

  $scope.$watch('model', function(val, old) {
    if (val && val !== old) {
      if ($scope.system['display_name']) {
        val['system'] = $scope.system['display_name'];
      }

      try {
        $scope.jsonValues.model = angular.toJson(val, 2);
      } catch (e) {
        console.error('Error attempting to stringify the model');
      }
    }
  }, true);

  // This process of stringify / parse will break the optional model
  // functionality. It's only useful in dev mode so only enable it then
  if ($scope.config.debugMode === true) {
    $scope.$watch('jsonValues', function(val, old) {
      if (val && old) {
        if (val.schema !== old.schema) {
          try {
            $scope.schema = JSON.parse(val.schema);
          } catch (e) {
            console.log('schema doesn\'t parse');
          }
        }
        if (val.form !== old.form) {
          try {
            $scope.form = JSON.parse(val.form);
          } catch (e) {
            console.log('form doesn\'t parse');
          }
        }
      }
    }, true);
  }

  // Model instantiate button will emit this so need to listen for it
  $scope.$on('generateSF', generateSF);

  // Stop the loading animation after the schema form is done
  $scope.$on('sf-render-finished', () => {
    $scope.response = tempResponse;
  });

  $scope.successCallback(command);
};
