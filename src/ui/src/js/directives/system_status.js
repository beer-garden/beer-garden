import template from "../../templates/system_status.html";

/**
 * systemStatusDirective - Directive for rendering system status.
 * @return {Object}  Directive for Angular.
 */
export default function systemStatusDirective() {
  return {
    restrict: "E",
    scope: {
      status: "=target",
    },
    template: template,
    link: function (scope, element, attrs) {
      scope.$watch("status", function () {
        switch (scope.status) {
          case "RUNNING":
            scope.labelClass = "label-success";
            break;
          case "STOPPING":
          case "UNRESPONSIVE":
            scope.labelClass = "label-warning";
            break;
          case "STARTING":
          case "INITIALIZING":
            scope.labelClass = "label-info";
            break;
          case "RELOADING":
            scope.labelClass = "label-primary";
            break;
          case "DEAD":
          case "STOPPED":
            scope.labelClass = "label-danger";
            break;
        }
      });
    },
  };
}
