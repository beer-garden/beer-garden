import angular from 'angular';

sfPostProcessor.$inject = ['postProcess', 'schemaForm'];
export function sfPostProcessor(postProcess, schemaForm) {

  postProcess.addPostProcess(function(canonicalForm) {

    // Validators
    var requiredAllowNull = function(modelValue, viewValue) {
      return !(modelValue === undefined);
    };
    var failNull = function(modelValue, viewValue) {
      return !(modelValue === null);
    }

    // Parsers
    var emptyStringToNull = function(modelValue) {
      return modelValue === '' ? null : modelValue;
    }

    for(var i=0; i<canonicalForm.length; i++) {
      schemaForm.traverseForm(canonicalForm[i], function(formObj) {
        if(formObj.schema) {

          var validators = {};
          if(!!formObj.schema.requiredAllowNull) {
            validators['requiredAllowNull'] = requiredAllowNull;
          }
          if(!!formObj.schema.failNull) {
            validators['failNull'] = failNull;
          }
          formObj.$validators = angular.merge({}, formObj.$validators, validators);

          var parsers = [];
          if(formObj.schema.type.indexOf('string') != -1 && formObj.schema.nullable) {
            parsers.push(emptyStringToNull);
          }
          formObj.$parsers = formObj.$parsers === undefined ? parsers : formObj.$parsers.concat(parsers);
        }
      });
    }
    return canonicalForm;
  });
};

sfErrorMessageConfig.$inject = ['sfErrorMessageProvider'];
export function sfErrorMessageConfig(sfErrorMessageProvider) {
  sfErrorMessageProvider.setDefaultMessage('requiredAllowNull', 'Required');
  sfErrorMessageProvider.setDefaultMessage('failNull', 'Required');
};

sfBuilderService.$inject = ['$rootScope', 'sfPath', 'UtilityService'];
export function sfBuilderService($rootScope, sfPath, UtilityService) {

  var SFBuilderService = {};

  /**
   * Returns a valid schema / form combination for use in angular-schema-form
   *
   * If there are optional fields, it will return a form which includes tabs
   * where the required and optional fields are separated.
   * If there are no * optional fields, then it returns a simple flat form with
   * the required fields only.
   *
   * @param {Object} system - A valid beer-garden System object
   * @param {Object} command - A valid beer-garden Command object
   * @returns {Object} schemaForm - An object with schema and form properties
   */
  SFBuilderService.build = function(system, command) {

    // Build the actual schema and form for this specific command
    var modelSF = SFBuilderService.buildModelSF(command, ['parameters']);

    // Merge the two into the final representation
    // For the schema start with common and add the model to its parameters
    // If the command has a custom schema then use that instead of the generated one
    if(command.schema !== undefined && !angular.equals({}, command.schema)) {
      var modelSchema = {type: 'object', properties: command.schema};
    }
    else {
      var modelSchema = {type: 'object', properties: modelSF['schema']};
    }

    // Form is a little more tricky
    // If the command has a custom form then use that instead of the generated one
    if(command.form !== undefined && !angular.equals({}, command.form) && !angular.equals([], command.form)) {
      var modelForm = angular.isArray(command.form) ? command.form : [command.form];
    }
    else {
      var modelForm = [], required = [], optional = [];

      angular.forEach(modelSF['form'], function(item) {
        // Form items can be either a string or dictionary with a key parameter
        var itemKey = typeof item === 'string' ? item : item.key;

        // The actual key itself should be an array, but if not we need to make it one
        itemKey = typeof itemKey === 'string' ?  sfPath.parse(itemKey) : itemKey;
        var schemaItem = modelSchema['properties'][itemKey[itemKey.length-1]];

        if(schemaItem.optional) {
          optional.push(item);
        }
        else {
          required.push(item);
        }
      });

      if(optional.length) {
        if(!required.length) {
          required.push({ 'type': 'help', 'helpvalue': '<div uib-alert class="alert alert-info m-b-0">None! :)</div>' });
        }
        modelForm.push({
          'type': 'tabs',
          'tabs': [
            {'title': 'Required Fields', 'items': required},
            {'title': 'Optional Fields', 'items': optional}
          ]
        });
      }
      else {
        modelForm = required;
      }
    }

    // Build the schema and form common to all commands
    var commonSF = SFBuilderService.buildCommonSF(system, command);

    // Tie in the model schema in the correct place
    commonSF['schema']['parameters'] = modelSchema;

    return {
      schema: { type: 'object', properties: commonSF['schema'] },
      form: modelForm.concat(commonSF['form'])
    };
  };

  /**
  * Builds the schema and form common to all commands.
  */
  SFBuilderService.buildCommonSF = function(system, command) {

    // SCHEMA
    var instance_names = [];
    angular.forEach(system.instances, function(instance){
      instance_names.push(instance.name);
    });

    var commonSchema = {
      'system': { 'title': 'System Name', 'type': 'string', 'default': system.name, 'required': true },
      'system_version': { 'title': 'System Version', 'type': 'string', 'default': system.version, 'required': true },
      'command': { 'title': 'Command Name', 'type': 'string', 'default': command.name, 'required': true },
      'comment': { 'title': 'Comment', 'type': 'string', 'default': '', 'required': false, 'maxLength': 140,
        'validationMessage': 'Maximum comment length is 140 characters' },
      'output_type': { 'title': 'Output Type', 'type': 'string', 'default': command.output_type, 'required': false },
      'instance_name': { 'title': 'Instance Name', 'type': 'string', 'required': true }
    };

    if(system.instances.length == 1) {
      commonSchema['instance_name']['default'] = instance_names[0];
      commonSchema['instance_name']['readonly'] = true;
    }

    // FORM
    var instance_help = {
       'type': 'help', 'helpvalue': '<div uib-alert class="alert alert-warning m-b-0">Instance is not RUNNING, but you can still "Make Request"</div><br>', 'condition': "checkInstance(instance_name)"
    };

    var systemSection = {
      'type': 'section',
      'htmlClass': 'row',
      'items' : [
        { 'key': 'system', 'feedback': false, 'disableSuccessState': true, 'disableErrorState': true, 'readonly': true, 'required': true, 'htmlClass': 'col-md-3' },
        { 'key': 'system_version',  'feedback': false, 'disableSuccessState': true, 'disableErrorState': true, 'readonly': true, 'required': true, 'htmlClass': 'col-md-3' },
        { 'key': 'command', 'feedback': false, 'disableSuccessState': true, 'disableErrorState': true, 'readonly': true, 'required': true, 'htmlClass': 'col-md-3' },
        { 'key': 'instance_name', 'feedback': false, 'disableSuccessState': true, 'htmlClass': 'col-md-3', 'type': 'select', 'choices': {'titleMap': instance_names}}
      ]
    };

    var hr = { 'type': 'help', 'helpvalue': '<hr>' };
    var comment = { 'key': 'comment', 'type': 'textarea', 'feedback': true, 'disableSuccessState': false,
      'disableErrorState': false, 'readonly': false, 'required': false, 'fieldHtmlClass': 'm-b-3' }

    var buttonSection = {
      'type': 'section',
      'htmlClass': 'row',
      'items': [
        { 'type': 'button', 'style': 'btn-warning w-100 ', 'title': 'Reset', 'onClick': 'reset(ngform, model, system, command.data)', 'htmlClass': "col-md-2" },
        { 'type': 'submit', 'style': 'btn-primary w-100', 'title': 'Make Request', 'htmlClass': "col-md-10" }
      ]
    };

    var commonForm = { 'type': 'fieldset', 'items': [hr, systemSection, comment, instance_help, buttonSection] };

    return {
      schema: commonSchema,
      form: commonForm
    };
  };

  /**
   * Build a schema and form for an object model.
   */
  SFBuilderService.buildModelSF = function(model, parentKey) {

    var paramSchemas = {};
    var paramForms = [];

    for(var i=0, len=model.parameters.length; i<len; i++) {
      var parameter = model.parameters[i];
      var key = parameter.key;
      var sf = SFBuilderService.buildParameterSF(parameter, parentKey);

      paramSchemas[key] = sf['schema'];
      paramForms.push(sf['form']);
    }

    return {
      schema: paramSchemas,
      form: paramForms
    };
  };

  /**
  * Build a schema and form for an individual parameter.
  */
  SFBuilderService.buildParameterSF = function(parameter, parentKey, inArray) {

    // Schema and form that are the same across all parameters
    var generalSF = {
      'schema': {
        'title': parameter.display_name,
        'optional': parameter.optional,
        'nullable': parameter.nullable,
        'description': UtilityService.escapeHtml(parameter.description)
      },
      'form': {
        'key': parentKey.concat(parameter.key)
      }
    }

    if(inArray) {
      generalSF['form']['key'].push('');
    }

    // Type-specific schema / forms
    var builderFunction;
    if(parameter.multi && !inArray) {
      builderFunction = SFBuilderService.buildMultiParameterSF;
    }
    else if(parameter.parameters && parameter.parameters.length > 0) {
      builderFunction = SFBuilderService.buildModelParameterSF;
    }
    else {
      builderFunction = SFBuilderService.buildSimpleParameterSF;
    }

    return angular.merge({}, generalSF, builderFunction(parameter, parentKey, inArray));
  };

  // Build a schema and form for a parameter that's not a dictionary
  // and not an array
  SFBuilderService.buildSimpleParameterSF = function(parameter, parentKey, inArray) {

    var baseSF = baseSchemaForm(parameter.type);
    var schema = baseSF['schema'], form = baseSF['form'];

    // If the set a form_input_type, we apply it to the form
    applyConstraint(form, 'type', parameter.form_input_type)

    // Deal with 'requiredness'
    // ASF does some mangling before its 'required' validation, most annoyingly making empty strings appear undefined.
    // So we have our own validation based on if the parameter is optional and whether nulls are allowed.
    // Booleans special. The only way they could 'fail' would be if they were nullable with a null
    // default. If that's allowed it would require two clicks to be 'false' and look the same as how it started.
    if(schema['type'].indexOf('boolean') === -1) {
      if(!parameter.optional) {
        schema[parameter.nullable ? 'requiredAllowNull' : 'required'] = true;
      }

      if(!parameter.nullable) {
        schema['failNull'] = true;
      }
    }

    // Now we do some setup that only makes sense if we aren't inside an array, because if we are we want to apply
    // these things to the array itself, not this
    if(!inArray) {

      // Set up the default model value for this parameter
      // FYI - It's a good idea to only specify a default for things that need it, as a default can cause ASF to treat
      // the field differently.
      // Parameters with NO default will not show in the model preview until they get a value.
      var defaultValue = correctDefault(parameter, schema['type']);
      if(defaultValue !== undefined) {
        if(defaultValue !== null || parameter.nullable) {
          schema['default'] = defaultValue;
        }
      }

      // Now map constraints that depend on the type into the schema and form
      if(schema['type'].indexOf('string') !== -1) {
        applyConstraint(schema, 'maxLength', parameter['maximum']);
        applyConstraint(schema, 'minLength', parameter['minimum']);
        applyConstraint(schema, 'pattern', parameter['regex']);
      }
      else if(schema['type'].indexOf('integer') !== -1 || schema['type'].indexOf('number') !== -1) {
        applyConstraint(schema, 'maximum', parameter['maximum']);
        applyConstraint(schema, 'minimum', parameter['minimum']);
      }
    }

    // Now wire up dynamic choices
    if(parameter.choices && !angular.equals(parameter.choices, {})) {

      // First determine what form element to use
      if(parameter.choices.display) {
        if(parameter.choices.display === 'typeahead') {
          form['type'] = 'typeahead';
        } else if(parameter.choices.display === 'select') {
          form['type'] = 'select';
        } else {
          form['type'] = 'typeahead';
          console.error("Don't know how to render choices type '" +
            parameter.choices.type + "', defaulting to 'typeahead' " +
            "(valid options are 'typeahead' and 'select')");
        }
      } else {
        form['type'] = 'typeahead';
      }

      // Then determine if it should be strict (only really affects typeaheads)
      if(parameter.choices.strict) {
        form['strict'] = true;
      }

      // Then populate the choices
      // Simple case - static list of choices
      if(parameter.choices.type === 'static') {
        form['choices'] = { titleMap: parameter.choices.value };

        if(parameter.choices.details && parameter.choices.details.key_reference) {
          var field = parentKey + '.' + parameter.choices.details.key_reference;

          form['choices']['updateOn'] = field;
          form['choices']['transforms'] = [{lookupField: field}];
        }
      }

      // Get choices from a URL
      else if(parameter.choices.type === 'url') {
        form['choices'] = {
          updateOn: [],
          httpGet: {
            url: parameter.choices.details['address'],
            queryParameterFields: {}
          }
        };

        for(var i=0; i<parameter.choices.details['args'].length; i++) {
          var pair = parameter.choices.details['args'][i];
          var field = parentKey + '.' + pair[1];

          form['choices']['updateOn'].push(field);
          form['choices']['httpGet']['queryParameterFields'][pair[0]] = field;
        }
      }

      // Get choices by making a request to another command
      else if (parameter.choices.type === 'command') {

        form['choices'] = {
          updateOn: [],
          callback: {
            function: 'createRequestWrapper',
            arguments: [{
              command: parameter.choices.details['name'],
              parameterNames: []
            }],
            argumentFields: []
          }
        };

        for(var i=0; i<parameter.choices.details['args'].length; i++) {
          var pair = parameter.choices.details['args'][i];
          var field = parentKey + '.' + pair[1];

          form['choices']['updateOn'].push(field);
          form['choices']['callback']['argumentFields'].push(field);
          form['choices']['callback']['arguments'][0]['parameterNames'].push(pair[0]);
        }

        // If it's an object then it's a fully specified command
        if(typeof parameter.choices.value === 'object') {
          Object.assign(form['choices']['callback']['arguments'][0], {
            system: parameter.choices.value.system,
            system_version: parameter.choices.value.system_version,
            instance_name: parameter.choices.value.instance_name
          });
        }
      }
      else {
        console.error("Don't know how to handle parameter '%s' choices type (%s)",
          parameter.key, parameter.choices.type);
      }

      if(parameter.nullable && form['type'] === 'select') {
        if(!Array.isArray(form['choices']['transforms'])) {
          form['choices']['transforms'] = [];
        }

        form['choices']['transforms'].push('fixNull');
      }
    }

    return { schema: schema, form: form };
  };

  SFBuilderService.buildMultiParameterSF = function(parameter, parentKey) {

    // Multi parameters are represented as 'array' types with their real type
    // definition in the 'items' definition. So first we need to construct the
    // schema and form for this as if it weren't a multi.
    var nestedSF = SFBuilderService.buildParameterSF(parameter, parentKey, true);

    // Now tweak the result to make sense as an array item
    // We are assuming the default for this parameter is intended for the array,
    // so remove it from the child
    delete nestedSF['schema']['default'];

    // Tweak the display a bit so it looks better inside the array
    nestedSF['form']['notitle'] = true;
    nestedSF['form']['htmlClass'] = 'clear-right';
    delete nestedSF['schema']['description'];

    // A nullable object is a distinct thing and doesn't make sense inside an
    // array (would be the same as an empty array)
    if(nestedSF['schema']['type'] === 'object') {
      nestedSF['schema']['nullable'] = false;
    }

    var arraySF = {
      schema: {
        type: ['array', 'null'],
        items: nestedSF['schema']
      },
      form: {
        startEmpty: !!parameter.nullable,
        items: [ nestedSF['form'] ]
      }
    };

    // Only add a default if necessary, otherwise it breaks things
    var arrayDefault = correctDefault(parameter, 'array');
    if(arrayDefault !== undefined) {
      arraySF['schema']['default'] = arrayDefault;
      arraySF['form']['startEmpty'] = true;
    }

    // Add array constraints
    applyConstraint(arraySF['schema'], 'maxItems', parameter['maximum']);
    applyConstraint(arraySF['schema'], 'minItems', parameter['minimum']);

    return arraySF;
  };

  SFBuilderService.buildModelParameterSF = function(parameter, parentKey, inArray) {

    var newParentKey = inArray ? parentKey.concat(parameter.key, "") : parentKey.concat(parameter.key);
    var innerSF = SFBuilderService.buildModelSF(parameter, newParentKey);
    var objDefault = correctDefault(parameter, 'object');

    var form = {}, schema = {
      type: 'object',
      partition: '!optional',
      accordionHeading: 'Optional Fields',
      properties: innerSF['schema']
    };

    if(parameter.optional && parameter.nullable && angular.equals({}, objDefault) && !inArray) {
      schema['format'] = 'nullable';
    } else {
      schema['default'] = objDefault;
      form['items'] = innerSF['form'];
    }

    return { schema: schema, form: form };
  };

  // Get a basic schema and form for a given parameter type
  var baseSchemaForm = function(parameterType) {
    var type = parameterType.toLowerCase();

    var typeMap = {
      any: 'variant',
      integer: 'integer',
      float: 'number',
      boolean: 'boolean',
      dictionary: 'dictionary',
      string: 'string',
      date: 'integer',
      datetime: 'integer'
    };

    // We want the schema type to default to 'string' and always also allow 'null'.
    // That way we have finer-grained control over when null is allowed.
    var schema = {
      type: [typeMap[type] || 'string', 'null']
    };
    var form = {};

    // Certain types require additional options
    if(type === 'date') {
      schema['format'] = 'datetime';
      form['options'] = {format: 'MM/DD/YYYY'};
    }
    else if (type === 'datetime') {
      schema['format'] = 'datetime';
    }

    return { schema: schema, form: form };
  };

  var correctDefault = function(parameter, type) {

    switch(type) {
      case 'boolean':
        return parameter.nullable && parameter.default === null ? null : !!parameter.default;

      // If the default is null then default to an empty array
      // Otherwise create a deep copy of the default
      case 'array':
        if( !!parameter.default ) {
          return $.extend(true, [], parameter.default);
        } else if( parameter.default === null && parameter.nullable ) {
          return null;
        } else {
          return undefined;
        }

      // If default is defined then return a deep copy, otherwise an empty object
      case 'object':
        if( !!parameter.default ) {
          return $.extend(true, {}, parameter.default);
        } else {
          return {};
        }

      default:
        return parameter.default;
    }
  };

  var applyConstraint = function(object, createKey, paramValue) {
    if(angular.isDefined(paramValue) && paramValue !== null) {
      object[createKey] = paramValue;
    }
  };

  return SFBuilderService;
};
