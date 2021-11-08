export default function customOnChangeDirective() {
  return {
    restrict: "A",
    link: function (scope, element, attrs) {
      let onChangeFunc = scope.$eval(attrs.customOnChange);
      element.bind("change", onChangeFunc);
      element.on("$destroy", function () {
        element.off();
      });
    },
  };
}
