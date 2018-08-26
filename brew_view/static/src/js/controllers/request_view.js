import _ from 'lodash';
import {formatDate, formatJsonDisplay} from '../services/utility_service.js';

requestViewController.$inject = [
  '$scope',
  '$state',
  '$stateParams',
  '$timeout',
  '$animate',
  'RequestService',
  'SystemService',
];

/**
 * requestViewController - Angular Controller for viewing an individual Request.
 * @param  {$scope} $scope             Angular's $scope object.
 * @param  {$state} $state             Angular's $state object.
 * @param  {$stateParams} $stateParams Angular's $stateParams object.
 * @param  {$timeout} $timeout         Angular's $timeout object.
 * @param  {$animate} $animate         Angular's $animate object.
 * @param  {Object} RequestService     Beer-Garden Request Service.
 * @param  {Object} SystemService      Beer-Garden's System Service.
 */
export default function requestViewController(
    $scope,
    $state,
    $stateParams,
    $timeout,
    $animate,
    RequestService,
    SystemService) {
  $scope.service = RequestService;

  $scope.instanceStatus = undefined;
  $scope.timeoutRequest = undefined;

  $scope.children = [];
  $scope.childrenCollapsed = true;

  $scope.rawOutput = undefined;
  $scope.formattedOutput = '';
  $scope.formattedParameters = '';
  $scope.formattedAvailable = false;
  $scope.formatErrorTitle = undefined;
  $scope.formatErrorMsg = undefined;
  $scope.showFormatted = false;

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

  $scope.loadPreview = function(_editor) {
    formatJsonDisplay(_editor, true);
  };

  $scope.canRepeat = function(request) {
    if (request.system === 'beer_garden') {
      return false;
    }

    return RequestService.isComplete(request);
  };

  $scope.showInstanceStatus = function(request, instanceStatus) {
    return !$scope.canRepeat(request) && instanceStatus &&
      instanceStatus != 'RUNNING';
  }

  $scope.formatOutput = function() {
    $scope.formattedOutput = '';
    $scope.formattedAvailable = false;
    $scope.showFormatted = false;
    $scope.formatErrorTitle = undefined;
    $scope.formatErrorMsg = undefined;

    let rawOutput = $scope.data.output;

    try {
      if (rawOutput === undefined || rawOutput == null) {
        rawOutput = 'null';
      } else if ($scope.data.output_type == 'JSON') {
        try {
          let parsedOutput = JSON.parse($scope.data.output);
          rawOutput = $scope.stringify(parsedOutput);

          if ($scope.countNodes($scope.formattedOutput) < 1000) {
            $scope.formattedOutput = rawOutput;
            $scope.formattedAvailable = true;
            $scope.showFormatted = true;
          } else {
            $scope.formatErrorTitle = 'Output is too large for collapsible view';
            $scope.formatErrorMsg = 'This output is valid JSON, but it\'s so big that ' +
                                      'displaying it in the collapsible viewer would crash the ' +
                                      'page.';
          }
        } catch (err) {
          $scope.formatErrorTitle = 'This JSON didn\'t parse correctly';
          $scope.formatErrorMsg = 'beer-garden was expecting this output to be JSON but it ' +
                                    'doesn\'t look like JSON. If this is happening often please ' +
                                    'let the plugin developer know.';
        }
      } else if ($scope.data.output_type == 'STRING') {
        try {
          rawOutput = $scope.stringify(JSON.parse($scope.data.output));
        } catch (err) { }
      }
    } finally {
      $scope.rawOutput = rawOutput;
    }
  };

  $scope.formatDate = formatDate;

  $scope.successCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;

    $scope.setWindowTitle(
      $scope.data.command,
      ($scope.data.metadata.system_display_name || $scope.data.system),
      $scope.data.system_version,
      $scope.data.instance_name,
      'request',
    );

    $scope.formatOutput();
    $scope.formattedParameters = $scope.stringify($scope.data.parameters);

    // If request is not yet successful
    // We need to find system attached to request
    // And find out if the status of that instance is up
    if (!RequestService.isComplete(response.data)) {
      $scope.findSystem(response.data.system, response.data.system_version).then(
        (bareSystem) => {
          SystemService.getSystem(bareSystem.id, false).then(
            (systemObj) => {
              $scope.instanceStatus = _.find(
                systemObj.data.instances,
                {name: response.data.instance_name}
              ).status;
            }
          );
        }
      );
    }

    // If the children view is expanded we have to do a little update
    if (!$scope.childrenCollapsed) {
      $scope.children = response.data.children;
    }

    // If any request isn't done then we need to keep checking
    if ((!RequestService.isComplete(response.data)) ||
        (!_.every(response.data.children, RequestService.isComplete))) {
      $scope.timeoutRequest = $timeout(function() {
        RequestService.getRequest($stateParams.request_id)
          .then($scope.successCallback, $scope.failureCallback);
      }, 3000);
    } else {
      $scope.timeoutRequest = undefined;
    }
  };

  $scope.failureCallback = function(response) {
    $scope.response = response;
    $scope.data = response.data;

    $scope.rawOutput = undefined;
    $scope.formattedOutput = undefined;
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
      'command',
      {
        name: request.command,
        systemName: request.system,
        systemVersion: request.system_version,
        request: newRequest,
      }
    );
  };

  $scope.$on('$destroy', function() {
    if ($scope.timeoutRequest) {
      $timeout.cancel($scope.timeoutRequest);
    }
  });

  $scope.hasParent = function(request) {
    return request.parent !== undefined && request.parent !== null;
  };

  $scope.hasChildren = function(request) {
    return request.children !== undefined &&
           request.children !== null &&
           request.children.length > 0;
  };

  $scope.toggleChildren = function() {
    $animate.enabled($('#requestTable'), true);
    $scope.disableAnimation = $timeout(function() {
      $animate.enabled($('#requestTable'), false);
    }, 300);

    $scope.childrenCollapsed = !$scope.childrenCollapsed;

    if ($scope.childrenCollapsed) {
      $scope.children = [];
    } else {
      $scope.children = $scope.data.children;
    }
  };

  $scope.showColumn = function(property) {
    if ($scope.data[property] !== undefined && $scope.data[property] !== null) {
      return true;
    }

    let show = false;
    if ($scope.hasChildren($scope.data)) {
      $scope.data.children.forEach(function(child) {
        if (child[property] !== undefined && child[property] !== null) {
          show = true;
        }
      });
    }

    return show;
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

  function loadRequest() {
    $scope.response = undefined;
    $scope.data = {};

    RequestService.getRequest($stateParams.request_id)
      .then($scope.successCallback, $scope.failureCallback);
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
