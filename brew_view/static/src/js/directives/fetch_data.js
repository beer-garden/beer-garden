import _ from 'lodash';
import template from '../../templates/fetch_data.html';
import {responseState} from '../services/utility_service.js';

fetchDataDirective.$inject = ['$timeout', 'ErrorService'];

export default function fetchDataDirective($timeout, ErrorService) {
  return {
    restrict: 'E',
    scope: {
      delay: '@?',
      response: '<',
    },
    template: template,
    link: function(scope, element, attrs) {
      scope.responseState = responseState;

      scope.emptyMap = ErrorService['empty'];
      scope.errorMap = ErrorService['error'];

      scope.errorGroup = function() {
        // There are some cases where we 'fake' a failure without actually
        // making a request. In those cases we'll just pass the error group.
        if (scope.response.errorGroup) {
          return scope.response.errorGroup;
        }
        if (_.includes(scope.response.config.url, 'system')) {
          return 'system';
        }
      }

      scope.errorMessage = function() {
        return _.get(scope.response.data, 'message', scope.response.data);
      }

      const delay = _.isUndefined(scope.delay) ? 0.25 : parseFloat(scope.delay);

      if (!delay) {
        scope.showSpin = true;
      } else {
        $timeout(() => {
          scope.showSpin = true;
        }, delay * 1000);
      }
    },
  };
};
