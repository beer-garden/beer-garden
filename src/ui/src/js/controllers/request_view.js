import _ from 'lodash';
import sizeOf from 'object-sizeof';
import {formatDate, formatJsonDisplay} from '../services/utility_service.js';

requestViewController.$inject = [
  '$scope',
  '$state',
  '$stateParams',
  '$timeout',
  '$animate',
  '$sce',
  'localStorageService',
  'RequestService',
  'SystemService',
  'EventService',
];

/**
 * requestViewController - Angular Controller for viewing an individual Request.
 * @param  {$scope} $scope             Angular's $scope object.
 * @param  {$state} $state             Angular's $state object.
 * @param  {$stateParams} $stateParams Angular's $stateParams object.
 * @param  {$timeout} $timeout         Angular's $timeout object.
 * @param  {$animate} $animate         Angular's $animate object.
 * @param  {Object} $sce              Angular's $sce object.
 * @param  {Object} localStorageService  Storage service
 * @param  {Object} RequestService     Beer-Garden Request Service.
 * @param  {Object} SystemService      Beer-Garden's System Service.
 * @param  {Object} EventService       Beer-Garden's Event Service.
 */
export default function requestViewController(
    $scope,
    $state,
    $stateParams,
    $timeout,
    $animate,
    $sce,
    localStorageService,
    RequestService,
    SystemService,
    EventService,) {

  $scope.request = undefined;
  $scope.complete = false;
  $scope.instanceStatus = undefined;
  $scope.timeoutRequest = undefined;
  $scope.children = [];
  $scope.filename = '';
  $scope.downloadVisible = false;
  $scope.childrenDisplay = [];
  $scope.childrenCollapsed = false;
  $scope.rawOutput = undefined;
  $scope.htmlOutput = '';
  $scope.jsonOutput = '';
  $scope.expiration_date = '';
  $scope.showDateModal = false;
  $scope.newExpirationDate = null;
  $scope.formattedParameters = '';
  $scope.formattedAvailable = false;
  $scope.formatErrorTitle = undefined;
  $scope.formatErrorMsg = undefined;
  $scope.showFormatted = false;
  $scope.disabledPourItAgain = false;
  $scope.msgPourItAgain = null;
  $scope.schema = {
                      'type': 'object',
                      'properties': {
                      'expiration_date': {
                              'title': ' ',
                              'type': ['integer', 'null'],
                              'format': 'datetime',
                            },
                      },
                  };
  $scope.form = [
                    {
                      'type': 'section',
                      'htmlClass': 'row',
                      'items': [
                        {'key': 'expiration_date'},
                      ],
                    },
                    {
                      'type': 'section',
                      'htmlClass': 'row',
                      'items': [
                        {
                          'type': 'submit', 'style': 'btn-primary w-100',
                          'title': 'Update Expiration',
                        },
                      ],
                    },
                ];
  $scope.model = {};

  $scope.isMaximized = localStorageService.get('isMaximized');
  if ($scope.isMaximized === null) {
    $scope.isMaximized = false;
  }
  $scope.displayOutput = localStorageService.get('displayOutput');
  if ($scope.displayOutput === null) {
    $scope.displayOutput = true;
  }
  $scope.displayParameter = localStorageService.get('displayParameter');
  if ($scope.displayParameter === null) {
    $scope.displayParameter = true;
  }

  $scope.statusDescriptions = {
    'CREATED': 'The request has been validated by beer-garden and is on the ' +
               'queue awaiting processing.',
    'RECEIVED': 'Not used.',
    'IN_PROGRESS': 'The request has been received by the plugin and is ' +
                   'actively being processed.',
    'CANCELED': 'The request has been canceled and will not be processed.',
    'SUCCESS': 'The request has completed successfully',
    'ERROR': 'The request encountered an error during processing and will ' +
             'not be reprocessed.',
  };

  $scope.formatDate = formatDate;

  $scope.loadPreview = function(_editor) {
    formatJsonDisplay(_editor, true);
  };

  $scope.updateExpirationDate = function(form, model){
    RequestService.updateRequest($scope.request, model.expiration_date);
  }

  $scope.showAlert = function() {
    let expired = ($scope.request.expiration_date <= ((new Date()).getTime())) && $scope.request.expiration_date;
    if (expired){
        $scope.expiration_date = 'Expired';
    }
    return expired
  }

  $scope.canRepeat = function(request) {
    return RequestService.isComplete(request);
  };
  
  $scope.resize = function(resizeCell) {
    $scope.isMaximized = !$scope.isMaximized;

    if (resizeCell == "parameterCell"){
      $scope.displayOutput = !$scope.displayOutput;
    }else if (resizeCell == "outputCell"){
      $scope.displayParameter = !$scope.displayParameter;
    }

    localStorageService.set('isMaximized', $scope.isMaximized);
    localStorageService.set('displayOutput', $scope.displayOutput);
    localStorageService.set('displayParameter', $scope.displayParameter);
  };

  $scope.showInstanceStatus = function(request, instanceStatus) {
    return !$scope.canRepeat(request) && instanceStatus &&
      instanceStatus != 'RUNNING';
  };

  $scope.formatOutput = function() {
    $scope.htmlOutput = '';
    $scope.jsonOutput = '';
    $scope.formattedAvailable = false;
    $scope.showFormatted = false;
    $scope.formatErrorTitle = undefined;
    $scope.formatErrorMsg = undefined;

    let rawOutput = $scope.request.output;

    try {
      if (rawOutput === undefined || rawOutput == null) {
        rawOutput = 'null';
      }
      else if ($scope.request.output_type == 'HTML') {
        $scope.formattedAvailable = true;
        $scope.showFormatted = true;

        // This is necessary for things like scripts and forms
        if ($scope.config.executeJavascript) {
          $scope.htmlOutput = $sce.trustAsHtml(rawOutput);
        } else {
          $scope.htmlOutput = rawOutput;
        }
      } else if ($scope.request.output_type == 'JSON') {
        try {
          let parsedOutput = JSON.parse(rawOutput);
          rawOutput = $scope.stringify(parsedOutput);
          if ($scope.countNodes($scope.formattedOutput) < 1000) {
            $scope.jsonOutput = rawOutput;
            $scope.formattedAvailable = true;
            $scope.showFormatted = true;
          } else {
            $scope.formatErrorTitle = 'Output is too large for collapsible view';
            $scope.formatErrorMsg = 'This output is valid JSON, but it\'s so big that ' +
                                      'displaying it in the collapsible viewer would crash the ' +
                                      'page. Downloading File might take a minute for UI to prepare.';
          }
        } catch (err) {
          $scope.formatErrorTitle = 'This JSON didn\'t parse correctly';
          $scope.formatErrorMsg = 'beer-garden was expecting this output to be JSON but it ' +
                                    'doesn\'t look like JSON. If this is happening often please ' +
                                    'let the plugin developer know.';
        }
      } else if ($scope.request.output_type == 'STRING') {
        try {
          rawOutput = $scope.stringify(JSON.parse(rawOutput));
        } catch (err) { }
      }
    } finally {
      $scope.rawOutput = rawOutput;
    }
  };

  $scope.successCallback = function(request) {
    $scope.request = request;
    $scope.expiration_date = formatDate($scope.request.expiration_date)
    $scope.model = {"expiration_date": $scope.request.expiration_date}
    $scope.filename = $scope.request.id;
    let namespace = $scope.request.namespace || $scope.config.gardenName;
    let request_system = SystemService.findSystem(namespace, $scope.request.system,
                         $scope.request.system_version);
    if (request_system != undefined) {
        let commands = request_system.commands;
        for (let i = 0; i < commands.length; i++) {
            if (commands[i].name == request.command){
                $scope.disabledPourItAgain = false;
                $scope.msgPourItAgain = null;
                break;
            }
            else {
                $scope.disabledPourItAgain = true;
                $scope.msgPourItAgain = 'Unable to find command';
            }
        }
    } else {
        $scope.disabledPourItAgain = true;
        $scope.msgPourItAgain = 'Unable to find system';
    }
    $scope.setWindowTitle(
      $scope.request.command,
      ($scope.request.metadata.system_display_name || $scope.request.system),
      $scope.request.system_version,
      $scope.request.instance_name,
      'request'
    );

    if (RequestService.isComplete($scope.request)) {

      if (sizeOf(request) > 5000000) {
        $scope.formatErrorTitle = 'Output is too large';
        $scope.formatErrorMsg = 'The output for this request is too large to display, please download instead';
      } else {
        $scope.formatOutput();
      }

      if ($scope.request.output) {
        $scope.downloadVisible = true;

        if ($scope.request.output_type == 'STRING') {
          $scope.filename += ".txt";
        } else if ($scope.request.output_type == 'HTML') {
          $scope.filename += ".html";
        } else if ($scope.request.output_type == 'JSON') {
          $scope.filename += ".json";
        }
      }

      $scope.complete = true;
    }

    $scope.formattedParameters = $scope.stringify($scope.request.parameters);

    // Grab the status of the instance this request targets to display if necessary
    let system = SystemService.findSystem(
      $scope.request.namespace, $scope.request.system, $scope.request.system_version,
    );
    $scope.instanceStatus = _.find(system.instances, {name: $scope.request.instance_name}).status;

    // Need to update the children list, but don't update if it's empty - Events don't
    // send children so the final REQUEST_COMPLETED update would clobber the list
    if ($scope.request.children) {
      $scope.children = $scope.request.children;

      if (!$scope.childrenCollapsed) {
        $scope.childrenDisplay = $scope.request.children;
      }
    }
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.request = response.data;

    $scope.rawOutput = undefined;
    $scope.htmlOutput = undefined;
    $scope.jsonOutput = undefined;
    $scope.formattedAvailable = false;
    $scope.showFormatted = false;
    $scope.formatErrorTitle = undefined;
    $scope.formatErrorMsg = undefined;

    $scope.setWindowTitle();
  };

  $scope.redoRequest = function(request) {
    const newRequest = {
      system: request.system,
      system_version: request.system_version,
      command: request.command,
      instance_name: request.instance_name,
      comment: request.comment || '',
      parameters: request.parameters,
    };
    $state.go(
      'base.command',
      {
        systemName: request.system,
        systemVersion: request.system_version,
        commandName: request.command,
        namespace: request.namespace || $scope.config.gardenName,  // Fix for v2 requests w/o a namespace
        request: newRequest,
      }
    );
  };

  $scope.childrenExist = function(children) {
    return children !== undefined &&
           children !== null &&
           children.length > 0;
  };

  $scope.toggleChildren = function() {
    $animate.enabled($('#requestTable'), true);
    $scope.disableAnimation = $timeout(function() {
      $animate.enabled($('#requestTable'), false);
    }, 300);

    $scope.childrenCollapsed = !$scope.childrenCollapsed;

    if ($scope.childrenCollapsed) {
      $scope.childrenDisplay = [];
    } else {
      $scope.childrenDisplay = $scope.children;
    }
  };

  // Return true if any of the children or the parent have an error_class
  $scope.showErrorColumn = function(request, children) {
    return _.some(_.concat(children, [request]), 'error_class');
  };

  $scope.hasParent = function(request) {
    return request.parent !== undefined && request.parent !== null;
  };

  $scope.getParentTree = function(request) {
    if (!$scope.hasParent(request)) {
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
    if (typeof obj != 'object') {
      return 1;
    }

    let total = 1;
    for (const key of Object.keys(obj)) {
      total += $scope.countNodes(object[key]);
    }
    return total;
  };

  function eventCallback(event) {
    if (event.name.startsWith('REQUEST')) {

      if (event.payload.id == $stateParams.requestId) {
        $scope.successCallback(event.payload);
      }
      else if (_.get(event, 'payload.parent.id') == $stateParams.requestId) {
        if (event.name == 'REQUEST_CREATED') {
          $scope.children.push(event.payload);
        } else {
          let child = _.find($scope.children, {id: event.payload.id});

          if (!child) {
            // If we missed the REQUEST_CREATED just push this one in there
            $scope.children.push(event.payload);
          } else {
            child.status = event.payload.status;
            child.updated_at = event.payload.updated_at;
            child.error_class = event.payload.error_class;
          }
        }

        if (!$scope.childrenCollapsed) {
          $scope.childrenDisplay = $scope.children;
        }
      }
    }
  }

  EventService.addCallback('request_view', (event) => {
    $scope.$apply(() => {eventCallback(event);})
  });
  $scope.$on('$destroy', function() {
    EventService.removeCallback('request_view');
  });

  function loadRequest() {
    $scope.response = undefined;
    $scope.request = {};

    RequestService.getRequest($stateParams.requestId).then(
      (response) => {
        $scope.response = response;
        $scope.successCallback(response.data);
      },
      $scope.failureCallback,
    );
  }

  $scope.$on('userChange', function() {
    loadRequest();
  });

  loadRequest();
};


/**
 * slideAnimation - Animation for sliding children.
 * @return {Object} with enter/leave functions.
 */
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
    },
  };
};
