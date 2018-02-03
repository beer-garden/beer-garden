import template from '../../templates/empty.html';

export default function emptyDirective() {
  return {
    restrict: 'E',
    scope: {
      loader: '=',
      label:  '@'
    },
    template: template
  };
};
