
utilityService.$inject = ['$rootScope', '$http'];

/**
 * utilityService - Used for getting configurations/icons and formatting
 * @param  {$rootScope} $rootScope Angular's $rootScope object
 * @param  {$http} $http           Angular's $http object
 * @return {Object}                For use by a controller.
 */
export default function utilityService($rootScope, $http) {
  let UtilityService = {};

  UtilityService.camelCaseKeys = function(o) {
    if (o instanceof Array) {
      return o.map(function(value) {
        if (typeof value === 'object') {
          value = camelCaseKeys(value);
        }
        return value;
      });
    } else {
      let newO = {};
      for (const origKey in o) {
        if (o.hasOwnProperty(origKey)) {
          let value = o[origKey];
          let newKey = origKey.replace(/(\_\w)/g, function(m) {
            return m[1].toUpperCase();
          });
          newO[newKey] = value;
        }
      }
      return newO;
    }
  };

  UtilityService.getConfig = function() {
    return $http.get('config');
  };

  UtilityService.login = function() {
    return $http.get('login');
  };

  UtilityService.logout = function() {
    return $http.get('logout');
  };

  UtilityService.getIcon = function(iconName) {
    if (iconName === undefined || iconName == null) {
      if ($rootScope.config === undefined || $rootScope.config.iconDefault === undefined) {
        return '';
      } else {
        iconName = $rootScope.config.iconDefault;
      }
    }

    return iconName.substring(0, iconName.indexOf('-')) + ' ' + iconName;
  };

  let re = /[&<>"'/]/g;
  let entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    '\'': '&#39;',
    '/': '&#x2F;',
  };

  UtilityService.escapeHtml = function(html) {
    if (html) {
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
      showPrintMargin: false,
    });
    _editor.setTheme('ace/theme/dawn');
    _editor.session.setMode('ace/mode/json');
    _editor.session.setUseWrapMode(true);
    _editor.session.setUseWorker(!readOnly);
    _editor.$blockScrolling = Infinity;

    if (readOnly) {
      _editor.renderer.$cursorLayer.element.style.opacity = 0;
    }
  };

  UtilityService.formatDate = function(timestamp) {
    if (timestamp) {
      return new Date(timestamp).toUTCString();
    }
  };

  /**
   * mapToArray - Transform two arrays, one of all possible values, one of
   * actual values, into an object with name -> boolean mapping
   * @param  {Array} array        Array with value list
   * @param  {Array} allPossible  Array with all possible values
   * @return {Object}             Object with name -> boolean mapping
   */
  UtilityService.arrayToMap = function(array, allPossible) {
    let map = {};
    for (let itemName of allPossible) {
      map[itemName] = _.indexOf(array, itemName) !== -1;
    }
    return map;
  };

  /**
   * mapToArray - Transform an object with name -> boolean mapping into an array
   * of the 'true' value names
   * @param  {Object} map  The object with name -> boolean mapping
   * @return {Array}       Array of 'true' value names
   */
  UtilityService.mapToArray = function(map) {
    return _.transform(map, (accumulator, value, key, obj) => {
      if (value) { accumulator.push(key); }
    }, []);
  };

  return UtilityService;
};
