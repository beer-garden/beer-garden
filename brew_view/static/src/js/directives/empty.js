import template from '../../templates/empty.html';

/**
 * emptyDirective - Directive for rendering empty 200's.
 * @return {Object}  Angular Directive
 */
export default function emptyDirective() {
  return {
    restrict: 'E',
    scope: {
      loader: '=',
      label: '@',
    },
    template: template,
  };
};
