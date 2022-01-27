export default function customOnChangeDirective() {
  return {
    restrict: 'A',
    link: function(scope, element, attrs) {
      const onChangeFunc = scope.$eval(attrs.customOnChange);
      element.bind('change', onChangeFunc);
      element.on('$destroy', function() {
        element.off();
      });
    },
  };
}
