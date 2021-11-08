import _ from "lodash";
import template from "../../templates/fetch_data.html";
import { responseState } from "../services/utility_service.js";

fetchDataDirective.$inject = ["$timeout", "ErrorService"];

export default function fetchDataDirective($timeout, ErrorService) {
  return {
    restrict: "E",
    scope: {
      closeable: "@?",
      delay: "@?",
      hide: "@?",
      response: "=",
    },
    template: template,
    link: function (scope, element, attrs) {
      // Do a little translation of the real state
      scope.responseState = function (response) {
        let realState = responseState(response);
        if (
          (_.includes(scope.hide, "loading") && realState === "loading") ||
          (_.includes(scope.hide, "empty") && realState === "empty")
        ) {
          return "success";
        }
        return realState;
      };

      scope.close = function () {
        scope.response.status = 200;
      };

      scope.getErrors = function (response) {
        let specific;
        let statusCode;

        // Do some simple translation to add extra items based on the url
        let url = _.get(response, "config.url");
        if (_.includes(url, "system")) {
          specific = "system";
        } else if (_.includes(url, "requests/")) {
          specific = "request";
        }

        if (scope.responseState(response) === "empty") {
          statusCode = "404";
        } else if (scope.responseState(response) === "error") {
          statusCode = response.status;
        }

        return ErrorService.getErrors(specific, statusCode);
      };

      scope.errorGroup = function () {
        // There are some cases where we 'fake' a failure without actually
        // making a request. In those cases we'll just pass the error group.
        if (scope.response.errorGroup) {
          return scope.response.errorGroup;
        }
        if (_.includes(scope.response.config.url, "system")) {
          return "system";
        }
      };

      scope.errorMessage = function () {
        return _.get(scope.response.data, "message", scope.response.data);
      };

      const delay = _.isUndefined(scope.delay) ? 0.25 : parseFloat(scope.delay);

      if (!delay) {
        scope.showSpin = true;
      } else {
        $timeout(() => {
          scope.showSpin = true;
        }, delay * 1000);
      }
    },
  };
}
