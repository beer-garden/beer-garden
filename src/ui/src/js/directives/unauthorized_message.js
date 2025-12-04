import template from '../../templates/401.html';


export default function unauthorizedDirective() {
  return {
    restrict: 'E',
    scope: {
      name: '@',
    },
    template: template,

  };
}
