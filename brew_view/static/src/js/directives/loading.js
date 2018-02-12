import angular from 'angular';
import template from '../../templates/loading.html';

loadingDirective.$inject = ['$timeout'];

/**
 * loadingDirective - Directive for rendering a loading spinner.
 * @param  {$timeout} $timeout Angular's $timeout Object.
 * @return {Object}            Angular Directive.
 */
export default function loadingDirective($timeout) {
  return {
    restrict: 'E',
    scope: {
      loader: '=',
      delay: '@?',
    },
    template: template,
    link: function(scope, element, attrs) {
      const delay = angular.isDefined(scope.delay) ? parseFloat(scope.delay) : 0.25;

      if (!delay) {
        scope.showSpin = true;
      } else {
        $timeout(function() {
          scope.showSpin = true;
        }, delay * 1000);
      }
    },
  };
};
