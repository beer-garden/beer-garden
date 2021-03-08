
gardenService.$inject = ['$http'];

/**
 * gardenService - Service for interacting with the garden API.
 * @param  {$http} $http Angular's $http object.
 * @return {Object}      Service for interacting with the garden API.
 */
export default function gardenService($http) {

  let GardenService = {};

  GardenService.getGardens = function(){
    return $http.get('api/v1/gardens/');
  }

  GardenService.getGarden = function(name){
    return $http.get('api/v1/gardens/' + name);
  }

  GardenService.createGarden = function(garden){
    return $http.post('api/v1/gardens', garden);
  }

  GardenService.updateGardenConfig = function(garden){
    return $http.patch('api/v1/gardens/' + garden.name, {operation: 'config', path: '', value: garden});
  }

  GardenService.syncGardens = function(){
    return $http.patch('api/v1/gardens', {operation: 'sync', path: '', value: ''})
  }

  GardenService.syncGarden = function(name){
    return $http.patch('api/v1/gardens/' + name, {operation: 'sync', path: '', value: ''})
  }

  GardenService.deleteGarden = function(name){
    return $http.delete('api/v1/gardens/' + name);
  }

  GardenService.serverModelToForm = function(model){

    var values = {};
    var stomp_headers = [];
    values['connection_type'] = model['connection_type'];
     if (model.hasOwnProperty('connection_params') && model.connection_params != null) {
        for (var parameter of Object.keys(model['connection_params']) ) {
          if (parameter == 'stomp_headers') {
            for (var key in model['connection_params'][parameter]) {
                stomp_headers[stomp_headers.length] = {'key': key,
                    'value': model['connection_params'][parameter][key]};
            }
            values[parameter] = stomp_headers;
          }
          else {
            values[parameter] = model['connection_params'][parameter];
          }
        }
    }

    return values;
  }

  GardenService.formToServerModel = function(model, form){

    model['connection_type'] = form['connection_type'];
    model['connection_params'] = {};
    var stomp_headers = {};
    for (var field of Object.keys(form) ) {
       if (field == 'stomp_headers') {
         for (var i in form[field]){
            stomp_headers[form[field][i]['key']] = form[field][i]['value'];
         }
         model['connection_params'][field] = stomp_headers;
       }
       else if (field != 'connection_type'){
         model['connection_params'][field] = form[field];
       }
    }

    return model;
  }

  GardenService.CONNECTION_TYPES = ['HTTP','STOMP','LOCAL'];

//  GardenService.stomp_header_array_to_dict = function(key, value){
//    GardenService.
//  }

  GardenService.SCHEMA = {
    'type': 'object',
    'required': [
      'connection_type'
    ],
    'properties': {
      'connection_type': {
        'title': 'Connection Type',
        'description': 'The type of connection that is established for the Garden to receive requests and events',
        'type': 'string',
        'enum': GardenService.CONNECTION_TYPES,
      },
      'name': {
        'title': 'Garden Name',
        'description': 'This is the globally routing name that Beer Garden utilizes when routing requests and events',
        'type': 'string',
      },
      'host': {
        'title': 'Host Name',
        'description': 'Beer-garden hostname',
        'type': 'string',
        'minLength': 1,
      },
      'port': {
        'title': 'Port',
        'description': 'Beer-garden port',
        'type': 'integer',
        'minLength': 1,
      },
      'stomp_host': {
              'title': 'Host Name',
              'description': 'Beer-garden hostname',
              'type': 'string',
              'minLength': 1,
            },
      'stomp_port': {
              'title': 'Port',
              'description': 'Beer-garden port',
              'type': 'integer',
              'minLength': 1,
            },
      'url_prefix': {
        'title': 'URL Prefix',
        'description': 'URL path that will be used as a prefix when communicating with Beer-garden. Useful if Beer-garden is running on a URL other than \'/\'.',
        'type': 'string',
      },
      'ca_cert': {
        'title': 'CA Cert Path',
        'description': 'Path to certificate file containing the certificate of the authority that issued the Beer-garden server certificate',
        'type': 'string',
      },
      'ca_verify': {
        'title': 'CA Cert Verify',
        'description': 'Whether to verify Beer-garden server certificate',
        'type': 'boolean',
      },
      'ssl': {
        'title': 'SSL Enabled',
        'description': 'Whether to connect with provided certifications',
        'type': 'boolean',
      },
      'client_cert': {
        'title': 'Client Cert Path',
        'description': 'Path to client certificate to use when communicating with Beer-garden',
        'type': 'string',
      },
      'stomp_send_destination': {
              'title': 'Send Destination',
              'description': 'Destination queue where Stomp will send messages.',
              'type': 'string',
      },
      'stomp_subscribe_destination': {
                    'title': 'Subscribe Destination',
                    'description': 'Destination queue where Stomp will listen for messages.',
                    'type': 'string',
      },
      'stomp_username': {
                    'title': 'Username',
                    'description': 'Username for Stomp connection.',
                    'type': 'string',
      },
      'stomp_password': {
                    'title': 'Password',
                    'description': 'Password for Stomp connection.',
                    'type': 'string',
      },
      'stomp_ssl': {
                          'title': ' ',
                                'type': 'object',
                                'properties':{
                                'use_ssl': {
                                              'title': 'SSL Enabled',
                                              'description': 'Whether to connect with provided certifications',
                                              'type': 'boolean',
                                },
                                'cert_file': {
                                              'title': 'Cert File Path',
                                              'description': 'Path to client certificate to use when communicating with Beer-garden',
                                              'type': 'string',
                                },
                                'private_key': {
                                              'title': 'Private key Path',
                                              'description': 'Path to client key to use when communicating with Beer-garden',
                                              'type': 'string',
                                },
                                'verify_host': {
                                              'title': 'Verify Host',
                                              'description': 'Whether to verify Host',
                                              'type': 'boolean',
                                },
                                'verify_hostname': {
                                              'title': 'Verify Hostname',
                                              'description': 'Whether to verify Hostname',
                                              'type': 'boolean',
                                },
                          },
      },
      'stomp_headers': {
                          'title': 'Headers',
                          'description': 'Headers to be sent with message',
                          'type': 'array',
                          'items':{
                              'title': ' ',
                              'type': 'object',
                              'properties': {
                                  'key': {
                                         'title': 'Key',
                                         'description': '',
                                         'type': 'string',
                                  },
                                  'value': {
                                         'title': 'Value',
                                         'description': '',
                                         'type': 'string',
                                  }
                              },
                          },
            },
      'user_mapping': {
                  'title': 'User Mapping',
                  'description': 'When forwarding/receiving requests, the owner of the Request will be mapped.',
                  'type': 'array',
                  'items':{
                      'title': ' ',
                      'type': 'object',
                      'properties': {
                          'key': {
                                 'title': 'Local Account',
                                 'description': '',
                                 'type': 'string',
                          },
                          'value': {
                                 'title': 'Remote Account',
                                 'description': '',
                                 'type': 'string',
                          }
                      },
                  },
            },
      'user_enable_mapping': {
              'title': 'Enable User Mapping',
              'description': 'Whether to map users for Requests',
              'type': 'boolean',
        },
      'user_default_local': {
              'title': 'Default Local User Mapping',
              'description': 'Default user mapping, if empty the default value will be Null',
              'type': 'string',
        },
      'user_default_remote': {
              'title': 'Default Remote User Mapping',
              'description': 'Default user mapping, if empty the default value will be Null',
              'type': 'string',
        },
    },

  }

  GardenService.FORM = [
    {
      'type': 'fieldset',
      'items': [
        'connection_type'
      ]
    },
    {
      'type': 'fieldset',
      'items': [
        {
          'type': 'tabs',
          'tabs': [
            {
              'title': 'HTTP',
              'items': [
                'host',
                'port',
                'url_prefix',
                'ssl',
                'ca_cert',
                'ca_verify',
                'client_cert'
              ],
            },
            {
              'title': 'STOMP',
              'items': [
                'stomp_host',
                'stomp_port',
                'stomp_send_destination',
                'stomp_subscribe_destination',
                'stomp_username',
                'stomp_password',
                'stomp_ssl',
                'stomp_headers',
              ],
            },
            {
              'title': 'User Mapping',
              'items': [
                'user_enable_mapping',
                'user_default_local',
                'user_default_remote',
                'user_mapping',
              ],
            },
          ],
        },
      ],
    },
    {
      'type': 'section',
      'htmlClass': 'row',
      'items': [
        {
          'type': 'submit', 'style': 'btn-primary w-100',
          'title': 'Save Configurations', 'htmlClass': 'col-md-10',
        },
      ],
    },
    ];

  return GardenService

};
