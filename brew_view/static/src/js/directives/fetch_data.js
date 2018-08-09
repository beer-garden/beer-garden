import _ from 'lodash';
import template from '../../templates/fetch_data.html';

fetchDataDirective.$inject = ['$timeout'];

export default function fetchDataDirective($timeout) {
  return {
    restrict: 'E',
    scope: {
      delay: '@?',
      loader: '=',
      label: '@',
    },
    template: template,
    link: function(scope, element, attrs) {
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
