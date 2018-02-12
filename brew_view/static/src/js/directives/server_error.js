import template from '../../templates/server_error.html';


/**
 * serverErrorDirective - Directive for rendering a server error.
 * @return {Object} Directive for Angular.
 */
export default function serverErrorDirective() {
  return {
    restrict: 'E',
    scope: {
      loader: '=',
    },
    template: template,
  };
};
