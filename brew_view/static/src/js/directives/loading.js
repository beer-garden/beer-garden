import angular from 'angular';
import template from '../../templates/loading.html';

loadingDirective.$inject = ['$timeout'];
export default function loadingDirective($timeout) {
  return {
    restrict: 'E',
    scope: {
      loader: "=",
      delay: "@?"
    },
    template: template,
    link: function(scope, element, attrs) {
      var delay = angular.isDefined(scope.delay) ? parseFloat(scope.delay) : 0.25;

      if(!delay) {
        scope.showSpin = true;
      }
      else {
        $timeout(function() {
          scope.showSpin = true;
        }, delay * 1000);
      }
    }
  };
};
