import template from '../../templates/login.html';

/**
 * loginDirective - Directive for rendering login widget
 * @return {Object}  Angular Directive
 */
export default function loginDirective() {
  return {
    restrict: 'E',
    scope: {
      login: '=loginInfo',
      submitFunc: '<',
    },
    template: template,
  };
};
