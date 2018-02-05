import template from '../../templates/server_error.html';

export default function serverErrorDirective() {
  return {
    restrict: 'E',
    scope: {
      loader: '='
    },
    template: template
  };
};
