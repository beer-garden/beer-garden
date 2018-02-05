
requestViewController.$inject = ['$scope', '$state', '$stateParams', '$timeout', '$animate', 'RequestService', 'UtilityService', 'SystemService'];
export default function requestViewController($scope, $state, $stateParams, $timeout, $animate, RequestService, UtilityService, SystemService) {
  $scope.request = {};
  $scope.request.errorMap = RequestService.errorMap;
  $scope.service = RequestService;
  $scope.timeoutRequest;
  $scope.children = [];
  $scope.children_collapsed = true;

  $scope.raw_output = undefined;
  $scope.formatted_output = "";
  $scope.formatted_parameters = "";
  $scope.formatted_available = false;
  $scope.format_error_title = undefined;
  $scope.format_error_msg = undefined;
  $scope.show_formatted = false;

  $scope.instance_status = "";
  $scope.status_descriptions = {
    "CREATED"     : "The request has been validated by beer-garden and is on the queue awaiting processing.",
    "RECEIVED"    : "Not used.",
    "IN_PROGRESS" : "The request has been received by the plugin and is actively being processed.",
    "CANCELED"    : "The request has been canceled and will not be processed.",
    "SUCCESS"     : "The request has completed successfully",
    "ERROR"       : "The request encountered an error during processing and will not be reprocessed."
  };

  $scope.loadPreview = function(_editor) {
    UtilityService.formatJsonDisplay(_editor, true);
  };

  $scope.canRepeat = function(request) {
    if(request.system === 'beer_garden') {
      return false;
    }

    if(RequestService.complete_statuses.indexOf(request.status) != -1) {
      return true;
    }

    return false;
  };

  $scope.formatOutput = function() {
    $scope.formatted_output = "";
    $scope.formatted_available = false;
    $scope.show_formatted = false;
    $scope.format_error_title = undefined;
    $scope.format_error_msg = undefined;

    var raw_output = $scope.request.data.output;

    try {
      if(raw_output === undefined || raw_output == null) {
        raw_output = 'null';
      }
      else if($scope.request.data.output_type == 'JSON') {
        try {
          var parsed_output = JSON.parse($scope.request.data.output);
          raw_output = $scope.stringify(parsed_output);

          if($scope.countNodes($scope.formatted_output) < 1000) {
            $scope.formatted_output = raw_output;
            $scope.formatted_available = true;
            $scope.show_formatted = true;
          } else {
            $scope.format_error_title = "Output is too large for collapsible view";
            $scope.format_error_msg = "This output is valid JSON, but it's so big that displaying it in the" +
            " collapsible viewer would crash the page."
          }
        }
        catch(err) {
          $scope.format_error_title = "This JSON didn't parse correctly";
          $scope.format_error_msg = "beer-garden was expecting this output to be JSON but it doesn't look like JSON." +
            " If this is happening often please let the plugin developer know.";
        }
      }
      // For version 1 we're assuming that STRING types are really JSON. But they don't get the special view
      else if($scope.request.data.output_type == 'STRING') {
        try {
          raw_output = $scope.stringify(JSON.parse($scope.request.data.output));
        }
        catch(err) { }
      }
    }
    finally {
      $scope.raw_output = raw_output;
    }
  };

  $scope.formatDate = function(timestamp) {
    if(timestamp) {
      return new Date(timestamp).toUTCString();
    }
  };

  $scope.successCallback = function(response) {
    $scope.request.data = response.data;
    $scope.request.loaded = true;
    $scope.request.error = false;
    $scope.request.status = response.status;
    $scope.request.errorMessage = '';

    $scope.formatOutput();
    $scope.formatted_parameters = $scope.stringify($scope.request.data.parameters);

    // If request is not yet successful
    // We need to find system attached to request
    // And find out if the status of that instance is up
    if(RequestService.complete_statuses.indexOf(response.data.status) == -1){

      // Get promise to get id of system associated with the response
      SystemService.getSystemID(response.data).then(function(systemId){

        // Using the system ID we can then get the system and instances
        SystemService.getSystem(systemId, false).then(function(systemObj){

          for(var i = 0; i < systemObj.data.instances.length; i++){

            if(systemObj.data.instances[i].name == response.data.instance_name){

              // It's possible the instance comes back up before we get here so we don't want to show it is running yet
              // So in the html we need to put an ngif against instance_status == 'RUNNING'
              $scope.instance_status = systemObj.data.instances[i].status;
            }
          }
        });
      });
    }

    // If the children view is expanded we have to do a little update
    if(!$scope.children_collapsed) {
      $scope.children = response.data.children;
    }

    // If request isn't done then we need to keep checking
    if(RequestService.complete_statuses.indexOf(response.data.status) == -1) {
      $scope.timeoutRequest = $timeout(function() {
        RequestService.getRequest($stateParams.request_id)
          .then($scope.successCallback, $scope.failureCallback);
      }, 3000);
    } else {
      $scope.timeoutRequest = undefined;
    }
  };

  $scope.failureCallback = function(response) {
    $scope.request.data = response.data;
    $scope.request.loaded = false;
    $scope.request.error = true;
    $scope.request.status = response.status;
    $scope.request.errorMessage = response.data.message;
    $scope.raw_output = undefined;
    $scope.formatted_output = undefined;
    $scope.formatted_available = false;
    $scope.show_formatted = false;
    $scope.format_error_title = undefined;
    $scope.format_error_msg = undefined;
  };

  $scope.redoRequest = function(request) {
    RequestService.getCommandId(request).then(
      function(id) {
        if(id !== null) {
          var newRequest = {
            system: request.system,
            system_version: request.system_version,
            command: request.command,
            instance_name: request.instance_name,
            comment: request.comment || '',
            parameters: request.parameters
          };

          $state.go('command', { command_id: id, request: newRequest });
        } else {
          alert("We're sorry, but this command no longer seems to exist.");
        }
      },
      function(data, status, headers, config) {
        alert("We're sorry, but a server error occurred trying to redirect you.");
      }
    );
  };

  $scope.$on('$destroy', function() {
    if($scope.timeoutRequest) {
      $timeout.cancel($scope.timeoutRequest);
    }
  });

  $scope.hasParent = function(request) {
    return request.parent !== undefined && request.parent !== null;
  };

  $scope.hasChildren = function(request) {
    return request.children !== undefined && request.children !== null && request.children.length > 0;
  };

  $scope.toggleChildren = function() {

    $animate.enabled($('#requestTable'), true);
    $scope.disableAnimation = $timeout(function() {
      $animate.enabled($('#requestTable'), false);
    }, 300);

    $scope.children_collapsed = !$scope.children_collapsed;

    if($scope.children_collapsed) {
      $scope.children = [];
    } else {
      $scope.children = $scope.request.data.children;
    }
  };

  $scope.showColumn = function(property) {
    if($scope.request.data[property] !== undefined && $scope.request.data[property] !== null) {
      return true;
    }

    var show = false;
    if($scope.hasChildren($scope.request.data)) {
      $scope.request.data.children.forEach(function(child) {
        if(child[property] !== undefined && child[property] !== null) {
          show = true;
        }
      });
    }

    return show;
  };

  $scope.getParentTree = function(request) {

    if(!$scope.hasParent(request)) {
      return [request];
    } else {
      return $scope.getParentTree(request.parent).concat(request);
    }
  };

  $scope.stringify = function(data) {
    return JSON.stringify(data, undefined, 2);
  };

  $scope.countNodes = function(obj) {
    // Arrays have type object too
    if(typeof obj != "object") {
      return 1;
    }

    var total = 1;
    for(var key in obj) {
      total += $scope.countNodes(obj[key]);
    }
    return total;
  };

  RequestService.getRequest($stateParams.request_id)
    .then($scope.successCallback, $scope.failureCallback);
};

export function slideAnimation() {
  return {
    enter: function(element, doneFn) {
      $(element).children('td').hide();
      $(element).children('td').slideDown(250);
      $(element).children('td').children('div').slideDown(250, function() {
        doneFn();
      });
    },
    leave: function(element, doneFn) {
      $(element).children('td').slideUp(250);
      $(element).children('td').children('div').slideUp(250, function() {
        doneFn();
      });
    }
  }
};
