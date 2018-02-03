import angular from 'angular';

commandViewController.$inject = ['$location', '$scope', '$state', '$stateParams', '$sce', 'CommandService',
   'RequestService', 'SystemService', 'SFBuilderService', 'UtilityService'];
export default function commandViewController($location, $scope, $state, $stateParams, $sce, CommandService,
    RequestService, SystemService, SFBuilderService, UtilityService ) {
  $scope.schema         = {};
  $scope.form           = [];
  $scope.model          = $stateParams.request || {};
  $scope.createError    = false;
  $scope.alerts         = [];
  $scope.baseModel      = {};
  $scope.system         = {};
  $scope.template       = '';
  $scope.manualOverride = false;
  $scope.manualModel    = '';

  $scope.jsonValues = {
    model: "",
    command: "",
    schema: "",
    form: ""
  };

  $scope.command = {
    data: [],
    loaded: false,
    status: null,
    error: false,
    errorMessage: '',
    errorMap: {
      'empty' : {
        'solutions' : [
          {
            problem     : 'ID is incorrect',
            description : 'The Backend has restarted and the ID changed of the command you were looking at',
            resolution  : 'Click the ' + $scope.config.application_name + ' logo at the top left and refresh the page'
          },
          {
            problem     : 'The Plugin Stopped',
            description : 'The plugin could have been stopped. You should probably contact the plugin ' +
                          'maintainer. You should be able to tell what\'s wrong by their logs. Plugins' +
                          ' are located at <code>$APP_HOME/plugins</code>',
            resolution  : '<kbd>less $APP_HOME/log/my-plugin.log</kbd>'
          }
        ]
      }
    }
  };

  $scope.createRequestWrapper = function(requestPrototype) {
    var request = {
      command: requestPrototype['command'],
      system: requestPrototype['system'] || $scope.system.name,
      system_version: requestPrototype['system_version'] || $scope.system.version,
      instance_name: requestPrototype['instance_name'] || 'default'
    };

    // If parameters are specified we need to use the model value
    if(angular.isDefined(requestPrototype['parameterNames'])) {
      request['parameters'] = {};
      var nameList = requestPrototype['parameterNames'];
      for(var i=0; i<nameList.length; i++) {
        request['parameters'][nameList[i]] = arguments[i+1]; // Skip the requestPrototype
      };
    }

    return RequestService.createRequestWait(request).then(
      function(response) { return response.data; }
    );
  };

  $scope.checkInstance = function(){

    // Loops through all system instances to find status of the model.instance
    for(var i=0; i < $scope.system.instances.length; i++){
        var instance = $scope.system.instances[i];

        // Checks status to show banner if not running, hide banner if running
        if(instance.name == $scope.model.instance_name){
            if(instance.status != "RUNNING"){
                return true;
            }
            else{
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
    var valid = true;
    if(!form.$valid) {
      angular.forEach(form.$error, function(errorGroup, errorKey) {
        if(errorKey !== 'schemaForm') {
          angular.forEach(errorGroup, function(error) {
            if(errorKey !== 'tv4-0' || !Array.isArray(error.$modelValue)) {
              valid = false;
            }
          });
        }
      });
    }

    if(valid) {
      $scope.createRequest(model)
    } else {
      $scope.alerts.push("Looks like there was an error validating the request.");
    }
  };

  $scope.createRequest = function(request) {
    if (typeof(request) === "string") {
      try {
        request = JSON.parse(request)
      } catch(err) {
        $scope.alerts.push(err);
        return
      }
    }
    var newRequest = angular.copy(request);

    newRequest['system'] = $scope.system['name'];
    if($scope.system['display_name']) {
      newRequest['metadata'] = {system_display_name: $scope.system['display_name']};
    }

    RequestService.createRequest(newRequest).then(
      function(response) {
        $location.path('/requests/' + response.data.id);
      },
      function(response) {
        $scope.createError = true;
        $scope.createErrorMessage = response.data.message;
      }
    );
  }

  $scope.reset = function(form, model, system, command) {
    $scope.alerts.splice(0);
    $scope.createError = false;
    $scope.model = {};

    generateSF();
    form.$setPristine();
  };

  $scope.closeAlert = function(index) {
    $scope.alerts.splice(index, 1);
  };

  $scope.loadPreview = function(_editor) {
    UtilityService.formatJsonDisplay(_editor, true);
  };

  $scope.loadEditor = function(_editor) {
    UtilityService.formatJsonDisplay(_editor, false);
  };

  $scope.toggleManualOverride = function(){
    $scope.alerts.splice(0);
    $scope.manualOverride = !$scope.manualOverride;
    $scope.manualModel = $scope.jsonValues.model;
  };

  var generateSF = function() {
    var sf = SFBuilderService.build($scope.system, $scope.command.data);
    $scope.schema = sf['schema'];
    $scope.form = sf['form'];

    $scope.jsonValues.schema = JSON.stringify($scope.schema, undefined, 2);
    $scope.jsonValues.form = JSON.stringify($scope.form, undefined, 2);
  };

  $scope.successCallback = function(response) {
    $scope.command.data = response.data;
    $scope.command.status = response.status;
    $scope.command.error = false;
    $scope.command.errorMessage = '';

    $scope.jsonValues.command = JSON.stringify($scope.command.data, undefined, 2);

    // If this command has a custom template then we're done!
    if($scope.command.data.template) {

      // This is necessary for things like scripts and forms
      if($scope.config.allow_unsafe_templates) {
        $scope.template = $sce.trustAsHtml($scope.command.data.template);
      }
      else {
        $scope.template = $scope.command.data.template;
      }

      $scope.command.loaded = true;
    }

    // Otherwise request the system and then generate the schema-form
    else {
      SystemService.getSystem(response.data.system.id, false).then(
        function(response) {
          $scope.system = response.data;
          generateSF();
        },
        $scope.failureCallback
      );
    }
  };

  $scope.failureCallback = function(response) {
    $scope.command.data = [];
    $scope.command.loaded = false;
    $scope.command.error = true;
    $scope.command.status = response.status;
    $scope.command.errorMessage = response.data.message;
  };

  $scope.$watch('model', function(val, old) {
    if(val && val !== old) {
      if($scope.system['display_name']) {
        val['system'] = $scope.system['display_name'];
      }

      try {
        $scope.jsonValues.model = angular.toJson(val, 2);
      } catch(e) {
        console.error("Error attempting to stringify the model");
      }
    }
  }, true);

  // This process of stringify / parse will break the optional model
  // functionality. It's only useful in dev mode so only enable it then
  if($scope.config.debug_mode === true) {
    $scope.$watch('jsonValues', function(val, old) {
      if(val && old) {
        if(val.schema !== old.schema) {
          try {
            $scope.schema = JSON.parse(val.schema);
          } catch(e) { console.log("schema doesn't parse"); }
        }
        if(val.form !== old.form) {
          try {
            $scope.form = JSON.parse(val.form);
          } catch(e) { console.log("form doesn't parse"); }
        }
      }
    }, true);
  }

  // Model instantiate button will emit this so need to listen for it
  $scope.$on('generateSF', generateSF);

  // Stop the loading animation after the schema form is done
  $scope.$on('sf-render-finished', function(){$scope.command.loaded = true;});

  CommandService.getCommand($stateParams.command_id)
    .then($scope.successCallback, $scope.failureCallback);
};
