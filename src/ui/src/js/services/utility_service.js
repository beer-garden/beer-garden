export function responseState(response) {
  if (_.isUndefined(response)) {
    return 'loading';
  }

  switch (response.status) {
    case 200:
      if (!_.isEmpty(response.data)) {
        return 'success';
      }
    // Fall through
    case 404:
      return 'empty';
    default:
      return 'error';
  }
}

/**
 * mapToArray - Transform two arrays, one of all possible values, one of
 * actual values, into an object with name -> boolean mapping
 * @param  {Array} array        Array with value list
 * @param  {Array} allPossible  Array with all possible values
 * @return {Object}             Object with name -> boolean mapping
 */
export function arrayToMap(array, allPossible) {
  const map = {};
  for (const itemName of allPossible) {
    map[itemName] = _.indexOf(array, itemName) !== -1;
  }
  return map;
}

/**
 * mapToArray - Transform an object with name -> boolean mapping into an array
 * of the 'true' value names
 * @param  {Object} map  The object with name -> boolean mapping
 * @return {Array}       Array of 'true' value names
 */
export function mapToArray(map) {
  return _.transform(
      map,
      (accumulator, value, key, obj) => {
        if (value) {
          accumulator.push(key);
        }
      },
      [],
  );
}

export function camelCaseKeys(o) {
  if (o instanceof Array) {
    return o.map(function(value) {
      if (typeof value === 'object') {
        value = camelCaseKeys(value);
      }
      return value;
    });
  } else {
    const newO = {};
    for (const origKey in o) {
      if (o.hasOwnProperty(origKey)) {
        const value = o[origKey];
        const newKey = origKey.replace(/(\_\w)/g, function(m) {
          return m[1].toUpperCase();
        });
        newO[newKey] = value;
      }
    }
    return newO;
  }
}

export function escapeHtml(html) {
  const re = /[&<>"'/]/g;
  const entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    '\'': '&#39;',
    '/': '&#x2F;',
  };

  if (html) {
    return String(html).replace(re, function(s) {
      return entityMap[s];
    });
  }
}

export function formatJsonDisplay(_editor, readOnly) {
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
}

export function formatDate(timestamp) {
  if (timestamp) {
    return new Date(timestamp).toUTCString();
  }
}

utilityService.$inject = ['$rootScope', '$http'];

/**
 * utilityService - Used for getting configurations/icons and formatting
 * @param  {$rootScope} $rootScope Angular's $rootScope object
 * @param  {$http} $http           Angular's $http object
 * @return {Object}                For use by a controller.
 */
export default function utilityService($rootScope, $http) {
  return {
    getConfig: () => {
      return $http.get('config');
    },
    getVersion: () => {
      return $http.get('version');
    },
    getNamespaces: () => {
      return $http.get('api/v1/namespaces');
    },
    getIcon: (iconName) => {
      if (iconName === undefined || iconName == null) {
        if (
          $rootScope.config === undefined ||
          $rootScope.config.iconDefault === undefined
        ) {
          return '';
        } else {
          iconName = $rootScope.config.iconDefault;
        }
      }

      return iconName.substring(0, iconName.indexOf('-')) + ' ' + iconName;
    },
  };
}
