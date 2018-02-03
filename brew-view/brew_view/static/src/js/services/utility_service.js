
utilityService.$inject = ['$rootScope', '$http'];
export default function utilityService($rootScope, $http) {
  var UtilityService = {};

  UtilityService.getConfig = function() {
    return $http.get('config');
  };

  UtilityService.getIcon = function(icon_name) {
    if(icon_name === undefined || icon_name == null) {
      if($rootScope.config === undefined || $rootScope.config.icon_default === undefined) {
        return "";
      } else {
        icon_name = $rootScope.config.icon_default;
      }
    }

    return icon_name.substring(0, icon_name.indexOf('-')) + ' ' + icon_name;
  };

  var re = /[&<>"'/]/g;
  var entityMap = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;",
    "/": "&#x2F;",
  };

  UtilityService.escapeHtml = function(html) {
    if(html) {
      return String(html).replace(re, function(s) {
        return entityMap[s];
      });
    }
  };

  UtilityService.formatJsonDisplay = function(_editor, readOnly) {
    _editor.setOptions({
      autoScrollEditorIntoView: true,
      highlightActiveLine: false,
      highlightGutterLine: false,
      minLines: 1,
      maxLines: 30,
      readOnly: readOnly,
      showLineNumbers: false,
      showPrintMargin: false
    });
    _editor.setTheme('ace/theme/dawn');
    _editor.session.setMode('ace/mode/json');
    _editor.session.setUseWrapMode(true);
    _editor.session.setUseWorker(!readOnly);
    _editor.$blockScrolling = Infinity;

    if(readOnly) {
      _editor.renderer.$cursorLayer.element.style.opacity = 0;
    }
  };

  return UtilityService;
};
