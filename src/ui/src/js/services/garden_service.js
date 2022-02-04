gardenService.$inject = ['$rootScope', '$http'];

/**
 * gardenService - Service for interacting with the garden API.
 * @param  {$rootScope} $rootScope    Angular's $rootScope object.
 * @param  {$http}      $http         Angular's $http object.
 * @return {Object}                   Service for interacting with the garden API.
 */
export default function gardenService($rootScope, $http) {
  const GardenService = {};

  GardenService.getGardens = function() {
    return $http.get('api/v1/gardens/');
  };

  GardenService.getGarden = function(name) {
    return $http.get('api/v1/gardens/' + encodeURIComponent(name));
  };

  GardenService.createGarden = function(garden) {
    return $http.post('api/v1/gardens', garden);
  };

  GardenService.updateGardenConfig = function(garden) {
    return $http.patch('api/v1/gardens/' + encodeURIComponent(garden.name), {
      operation: 'config',
      path: '',
      value: garden,
    });
  };

  GardenService.syncGardens = function() {
    return $http.patch('api/v1/gardens', {
      operation: 'sync',
      path: '',
      value: '',
    });
  };

  GardenService.syncGarden = function(name) {
    return $http.patch('api/v1/gardens/' + encodeURIComponent(name), {
      operation: 'sync',
      path: '',
      value: '',
    });
  };

  GardenService.deleteGarden = function(name) {
    return $http.delete('api/v1/gardens/' + encodeURIComponent(name));
  };

  GardenService.findGarden = function(name) {
    return _.find($rootScope.gardens, {name: name});
  };

  GardenService.importGardenConfig = (gardenDefinition, gardenConfigJson) => {
    const gardenName = encodeURIComponent(gardenDefinition['name']);
    const url = `api/v1/gardens/${gardenName}`;
    const gardenConfig = JSON.parse(gardenConfigJson);
    gardenDefinition['connection_params'] = gardenConfig;

    return $http.patch(url, {
      operation: 'config',
      path: '',
      value: gardenDefinition,
    });
  };

  GardenService.serverModelToForm = function(model) {
    const values = {};
    const stompHeaders = [];
    values['connection_type'] = model['connection_type'];
    if (
      model.hasOwnProperty('connection_params') &&
      model.connection_params != null
    ) {
      for (const parameter of Object.keys(model['connection_params'])) {
        if (parameter == 'stomp_headers') {
          // eslint-disable-next-line guard-for-in
          for (const key in model['connection_params']['stomp_headers']) {
            stompHeaders[stompHeaders.length] = {
              key: key,
              value: model['connection_params']['stomp_headers'][key],
            };
          }
          values['stomp_headers'] = stompHeaders;
        } else {
          // Recursively remove null/empty values from json payload
          const parameterValue = (function filter(obj) {
            Object.entries(obj).forEach(
                ([key, val]) =>
                  (val && typeof val === 'object' && filter(val)) ||
                ((val === null || val === '') && delete obj[key]),
            );
            return obj;
          })(model.connection_params[parameter]);

          values[parameter] = parameterValue;
        }
      }
    }

    return values;
  };

  const getSimpleFieldPredicate = (entryPointValues) => {
    // it's better to be explicit because of the inherent stupidity of
    // Javascript "truthiness"
    return (
      (entry) =>
        typeof entryPointValues[entry] === 'undefined' ||
            entryPointValues[entry] === null ||
            entryPointValues[entry] === ''
    );
  };

  const isEmptyObject = (obj) => {
    !!obj && !Object.keys(obj).length;
  };

  const isBlank = (entry) => !entry;

  const isEmptyStompHeaders = (headerEntry) => {
    const headersExist = !!headerEntry && 'headers' in headerEntry;
    const headersZeroLength = (
      !headersExist ||
      headerEntry['headers'].length === 0);
    const headersAllEmpty = (
      !headersZeroLength &&
      headerEntry['headers'].every(isEmptyObject)
    );
    const headersAllBlank = (
      !headersAllEmpty &&
      headerEntry['headers'].every(
          (entry) =>
            ('key' in entry && isBlank(entry['key'])) ||
            ('value' in entry && isBlank(entry['value'])))
    );

    return (
      !headersExist ||
      headersZeroLength ||
      headersAllEmpty ||
      headersAllBlank
    );
  };

  // eslint-disable-next-line no-unused-vars
  const cleanEmptyStompHeaders = () => 'TODO';

  const isEmptyStompConnection = (entryPointValues) => {
    /* If every field is missing, then obviously the stomp connection can be
     * considered empty.
     *
     * It gets a little more complicated in other cases because a lot of garbage
     * data is being passed around (an issue for another day).
     *
     * So we do a lot of checking of the corner cases in
     * isEmptyStompConnection and isEmptyStompHeaders so that the results of
     * this function is truly representative of whether we would consider the
     * connection to be "empty".
     *
     * (The point of all this is that if the connection meets our common-sense
     * definition of empty, then the resulting connection parameter object
     * won't even have a 'stomp' entry at all, which is far preferable to
     * polluting the database with the cruft that gets picked up in the UI.)
     */
    const simpleFieldMissing = getSimpleFieldPredicate(entryPointValues);

    const stompSimpleFields = [
      'host', 'password', 'port', 'send_destination', 'subscribe_destination',
      'username',
    ];
    const stompSslFields = ['ca_cert', 'client_cert', 'client_key'];

    const allSimpleFieldsMissing = stompSimpleFields.every(simpleFieldMissing);
    const headersMissing = isEmptyStompHeaders(entryPointValues);
    const sslIsMissing = typeof entryPointValues['ssl'] === 'undefined' ||
        !!Object.entries(entryPointValues['ssl']);
    let nestedFieldsMissing = true;

    if (!sslIsMissing) {
      nestedFieldsMissing = stompSslFields.every(
          (entry) =>
            typeof entryPointValues['ssl'][entry] === 'undefined' ||
            entryPointValues['ssl'][entry] === null ||
            entryPointValues['ssl'][entry] === '',
      );
    }

    const allStompFieldsEmpty = headersMissing && allSimpleFieldsMissing &&
        nestedFieldsMissing;

    return allStompFieldsEmpty;
  };

  const isEmptyHttpConnection = (entryPointValues) => {
    // Simply decide if every field in the http entry is blank.
    const simpleFieldMissing = getSimpleFieldPredicate(entryPointValues);
    const httpSimpleFields = [
      'ca_cert', 'client_cert', 'host', 'port', 'url_prefix',
    ];
    const allHttpFieldsEmpty = httpSimpleFields.every(simpleFieldMissing);

    return allHttpFieldsEmpty;
  };

  GardenService.formToServerModel = function(data, model) {
    /* Carefully pick apart the form data and translate it to the correct server
     * model. Throw an error if the entire form is empty (i.e., don't allow
     * empty connection parameters for both entry points on a remote garden).
     */
    const {connection_type: modelConnectionType, ...modelWithoutConxType} = model;
    let newModel = {...data};
    newModel['connection_type'] = modelConnectionType;

    const updatedConnectionParams = {};
    const emptyConnections = {};
    const emptyChecker = {
      'stomp': isEmptyStompConnection,
      'http': isEmptyHttpConnection,
    };

    for (const modelEntryPointName of Object.keys(modelWithoutConxType)) {
      // modelEntryPointName is either 'http' or 'stomp'
      const modelEntryPointMap = modelWithoutConxType[modelEntryPointName];
      const isEmpty = emptyChecker[modelEntryPointName](modelEntryPointMap);

      if (isEmpty) {
        emptyConnections[modelEntryPointName] = true;
        continue;
      } else {
        emptyConnections[modelEntryPointName] = false;
      }

      const updatedEntryPoint = {};

      for (const modelEntryPointKey of Object.keys(modelEntryPointMap)) {
        const modelEntryPointValue = modelEntryPointMap[modelEntryPointKey];

        if (modelEntryPointName === 'stomp' && modelEntryPointKey === 'headers') {
          // the ugly corner case is the stomp headers
          const formStompHeaders = modelEntryPointValue;
          const modelUpdatedStompHeaderArray = [];

          for (const formStompHeader of formStompHeaders) {
            const formStompKey = formStompHeader['key'];
            const formStompValue = formStompHeader['value'];

            // assume that we have both a key and a value or neither
            if (formStompKey && formStompValue) {
              modelUpdatedStompHeaderArray.push(
                  {
                    'key': formStompKey,
                    'value': formStompValue,
                  },
              );
            }
          }

          if (modelUpdatedStompHeaderArray.length > 0) {
            updatedEntryPoint['headers'] = modelUpdatedStompHeaderArray;
          }
        } else {
          updatedEntryPoint[modelEntryPointKey] = modelEntryPointValue;
        }
      }
      updatedConnectionParams[modelEntryPointName] = updatedEntryPoint;
    }

    newModel = {...newModel, 'connection_params': updatedConnectionParams};

    return newModel;
  };

  GardenService.CONNECTION_TYPES = ['HTTP', 'STOMP'];

  //  GardenService.stomp_header_array_to_dict = function(key, value){
  //    GardenService.
  //  }

  GardenService.SCHEMA = {
    type: 'object',
    required: ['connection_type'],
    properties: {
      connection_type: {
        title: 'Connection Type',
        description:
          'The type of connection that is established for the Garden to ' +
          'receive requests and events',
        type: 'string',
        enum: GardenService.CONNECTION_TYPES,
      },
      http: {
        title: ' ',
        type: 'object',
        properties: {
          name: {
            title: 'Garden Name',
            description:
              'This is the globally routing name that Beer Garden utilizes ' +
              'when routing requests and events',
            type: 'string',
          },
          host: {
            title: 'Host Name',
            description: 'Beer-garden hostname',
            type: 'string',
            minLength: 1,
          },
          port: {
            title: 'Port',
            description: 'Beer-garden port',
            type: 'integer',
            minLength: 1,
          },
          url_prefix: {
            title: 'URL Prefix',
            description:
              'URL path that will be used as a prefix when communicating ' +
              'with Beer-garden. Useful if Beer-garden is running on a URL ' +
              'other than \'/\'.',
            type: 'string',
          },
          ca_cert: {
            title: 'CA Cert Path',
            description:
              'Path to certificate file containing the certificate of the ' +
              'authority that issued the Beer-garden server certificate',
            type: 'string',
          },
          ca_verify: {
            title: 'CA Cert Verify',
            description: 'Whether to verify Beer-garden server certificate',
            type: 'boolean',
          },
          ssl: {
            title: 'SSL Enabled',
            description: 'Whether to connect with provided certifications',
            type: 'boolean',
          },
          client_cert: {
            title: 'Client Cert Path',
            description:
              'Path to client certificate to use when communicating with Beer-garden',
            type: 'string',
          },
        },
      },
      stomp: {
        title: ' ',
        type: 'object',
        properties: {
          host: {
            title: 'Host Name',
            description: 'Beer-garden hostname',
            type: 'string',
            minLength: 1,
          },
          port: {
            title: 'Port',
            description: 'Beer-garden port',
            type: 'integer',
            minLength: 1,
          },
          send_destination: {
            title: 'Send Destination',
            description: 'Destination queue where Stomp will send messages.',
            type: 'string',
          },
          subscribe_destination: {
            title: 'Subscribe Destination',
            description:
              'Destination queue where Stomp will listen for messages.',
            type: 'string',
          },
          username: {
            title: 'Username',
            description: 'Username for Stomp connection.',
            type: 'string',
          },
          password: {
            title: 'Password',
            description: 'Password for Stomp connection.',
            type: 'string',
          },
          ssl: {
            title: ' ',
            type: 'object',
            properties: {
              use_ssl: {
                title: 'SSL Enabled',
                description: 'Whether to connect with provided certifications',
                type: 'boolean',
              },
              ca_cert: {
                title: 'CA Cert',
                description:
                  'Path to certificate file containing the certificate of ' +
                  'the authority that issued the message broker certificate',
                type: 'string',
              },
              client_cert: {
                title: 'Client Cert',
                description:
                  'Path to client public certificate to use when communicating ' +
                  'with the message broker',
                type: 'string',
              },
              client_key: {
                title: 'Client Key',
                description:
                  'Path to client private key to use when communicating with ' +
                  'the message broker',
                type: 'string',
              },
            },
          },
          headers: {
            title: ' ',
            title: 'Headers',
            title: ' ',
            description: ' ',
            type: 'array',
            items: {
              title: ' ',
              type: 'object',
              properties: {
                key: {
                  title: 'Key',
                  description: '',
                  type: 'string',
                },
                value: {
                  title: 'Value',
                  description: '',
                  type: 'string',
                },
              },
            },
          },
        },
      },
    },
  };

  GardenService.FORM = [
    {
      type: 'fieldset',
      items: ['connection_type'],
    },
    {
      type: 'fieldset',
      items: [
        {
          type: 'tabs',
          tabs: [
            {
              title: 'HTTP',
              items: [
                'http.host',
                'http.port',
                'http.url_prefix',
                'http.ssl',
                'http.ca_cert',
                'http.ca_verify',
                'http.client_cert',
              ],
            },
            {
              title: 'STOMP',
              items: [
                'stomp.host',
                'stomp.port',
                'stomp.send_destination',
                'stomp.subscribe_destination',
                'stomp.username',
                'stomp.password',
                'stomp.ssl',
                {
                  'type': 'help',
                  'helpvalue': '<h4>Headers</h4><p>(Refresh browser if keys ' +
                  'and values are known to exist but are not populated on this' +
                  ' form)</p>',
                },
                'stomp.headers',
              ],
            },
          ],
        },
      ],
    },
    {
      type: 'section',
      htmlClass: 'row',
      items: [
        {
          type: 'submit',
          style: 'btn-primary w-100',
          title: 'Save Configuration',
          htmlClass: 'col-md-10',
        },
      ],
    },
  ];

  return GardenService;
}
