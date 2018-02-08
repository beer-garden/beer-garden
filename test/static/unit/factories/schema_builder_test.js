xdescribe("SchemaBuilder", function() {

  var builder, sandbox;

  beforeEach(module('bgApp'));
  beforeEach(inject(function(_SchemaBuilder_) {
    builder = _SchemaBuilder_
  }));

  beforeEach(function() {
    sandbox = sinon.sandbox.create();
  });

  afterEach(function() {
    sandbox.restore();
  });

  describe("build", function() {

    var command, system, buildDefaultSchema, buildCommandSchema;

    beforeEach(function() {
      command     = sinon.spy();
      system      = sinon.spy();
      buildDefaultSchema = sandbox.stub(builder, 'buildDefaultSchema');
      buildCommandSchema = sandbox.stub(builder, 'buildCommandSchema');
    });

    it("should call buildDefaultSchema with the correct parameters", function() {
      builder.build(system, command);
      sinon.assert.calledOnce(buildDefaultSchema);
      sinon.assert.calledWithExactly(buildDefaultSchema, system, command);
    });

    it("should call buildCommandSchema with the correct parameters", function() {
      builder.build(system, command);
      sinon.assert.calledOnce(buildCommandSchema);
      sinon.assert.calledWithExactly(buildCommandSchema, command);
    });

    it("should return a valid schema", function() {
      buildDefaultSchema.returns({});
      var schema = builder.build(system, command);
      expect(schema).to.have.property('type');
      expect(schema).to.have.property('properties');
      expect(schema['type']).to.equal('object');
      expect(schema['properties']).to.deep.equal({});
    });

    it("should update the defaultSchema with results from the buildCommandSchema", function() {
      buildDefaultSchema.returns({"foo":"bar"});
      buildCommandSchema.returns({"foo2":"bar2"});

      var schema = builder.build(system, command);
      expect(schema).to.have.property('properties');
      expect(schema['properties']).to.have.property('foo');
      expect(schema['properties']).to.have.property('foo2');
      expect(schema['properties']['foo']).to.equal('bar');
      expect(schema['properties']['foo2']).to.equal('bar2');
    });
  });// End Describe buildSchema

  describe("buildDefaultSchema", function() {

    var system, command;

    beforeEach(function() {
      system  = sinon.spy();
      command = sinon.spy();
    });

    xit("should generate a default schema with 4 items if there is no instance_name", function() {
      var defaultSchema = builder.buildDefaultSchema(system, command);
      var count = 0;
      for(var k in defaultSchema) { count += 1; }
      expect(count).to.equal(4);
      expect(defaultSchema).to.have.property('system');
      expect(defaultSchema).to.have.property('command');
    });

    it("should generate the correct system schema", function() {
      var defaultSchema = builder.buildDefaultSchema(system, command);
      var systemSchema  = defaultSchema['system'];

      expect(systemSchema).to.have.property('title');
      expect(systemSchema).to.have.property('type');
      expect(systemSchema).to.have.property('default');
      expect(systemSchema).to.have.property('required');

      expect(systemSchema.title).to.equal('System Name');
      expect(systemSchema.type).to.equal('string');
      expect(systemSchema.default).to.equal(system.name);
      expect(systemSchema.required).to.equal(true);
    });

    it("should generate the correct command schema", function() {
      var defaultSchema = builder.buildDefaultSchema(system, command);
      var commandSchema = defaultSchema['command'];

      expect(commandSchema).to.have.property('title');
      expect(commandSchema).to.have.property('type');
      expect(commandSchema).to.have.property('default');
      expect(commandSchema).to.have.property('required');

      expect(commandSchema.title).to.equal('Command Name');
      expect(commandSchema.type).to.equal('string');
      expect(commandSchema.default).to.equal(command.name);
      expect(commandSchema.required).to.equal(true);
    });

    xit("should generate an instance_name schema if one is defined", function() {
      system.instance_names = ['instance1', 'instance2']
      var defaultSchema = builder.buildDefaultSchema(system, command);
      var count = 0;
      for(var k in defaultSchema) { count += 1; }
      expect(defaultSchema).to.have.property('instance_name');
    });

    xit('should generate the correct instance_name schema if one is defined', function() {
      system.instance_names = ['instance1', 'instance2']
      var defaultSchema       = builder.buildDefaultSchema(system, command);
      var instanceNameSchema  = defaultSchema['instance_name']

      expect(instanceNameSchema).to.have.property('title');
      expect(instanceNameSchema).to.have.property('type');
      expect(instanceNameSchema).to.have.property('description');
      expect(instanceNameSchema).to.have.property('required');

      expect(instanceNameSchema.title).to.equal('Instance Name')
      expect(instanceNameSchema.type).to.equal('string')
      expect(instanceNameSchema.description).to.equal('The instance of ' + system.name +
                                                      ' you would like to process your request.')
      expect(instanceNameSchema.required).to.equal(true)
    });
  }); // End Describe buildDefaultSchema

  describe("buildCommandSchema", function() {

    var command, buildParameterSchema;

    beforeEach(function() {
      command = sinon.spy();
      buildParameterSchema = sinon.stub(builder, 'buildParameterSchema');
    });

    it("should create an empty parameter schema if there are no command parameters", function() {
      command.parameters  = [];
      var commandSchema   = builder.buildCommandSchema(command);
      var count = 0;
      for (var key in commandSchema) { count++; }
      expect(count).to.equal(1);
      expect(commandSchema).to.have.property('parameters');
      var parametersSchema = commandSchema['parameters'];

      expect(parametersSchema).to.have.property('type');
      expect(parametersSchema).to.have.property('title');
      expect(parametersSchema).to.have.property('properties');

      expect(parametersSchema.type).to.equal('object');
      expect(parametersSchema.title).to.equal('Parameters');
      expect(parametersSchema.properties).to.deep.equal({});
    });

    it("should setup the parametersSchema correctly if there are parameters", function() {
      command.parameters = [ {key:'param1'} ];
      buildParameterSchema.returns('parameterSchema')

      var commandSchema   = builder.buildCommandSchema(command);
      var count = 0;
      for (var key in commandSchema['parameters']['properties']) { count++; }
      expect(count).to.equal(1);

      var properties = commandSchema['parameters']['properties'];
      expect(properties).to.have.property('param1');
      expect(properties.param1).to.equal('parameterSchema');
    });

    it("should call buildParameterSchema with the correct values", function() {
      var parameter = {key: 'myKeyValue'}
      command.parameters = [ parameter ]
      var commandSchema = builder.buildCommandSchema(command);
      sinon.assert.calledOnce(buildParameterSchema)
      sinon.assert.calledWithExactly(buildParameterSchema, parameter, false, false);
    });
  }); // End Describe buildCommandSchema

  describe("buildParameterSchema", function() {

    var parameter;

    beforeEach(function() {
      parameter = sinon.spy();
      parameter.type = 'any';
    });

    describe("buildSimpleParameterSchema", function() {

      it("should set the title up correctly", function() {
        parameter.display_name = 'My Display Name';
        var schema = builder.buildParameterSchema(parameter, true, false);

        expect(schema).to.have.property('title');
        expect(schema.title).to.equal('My Display Name');
      });

      it("should set the description up correctly", function() {
        parameter.description = 'My Description';
        var schema = builder.buildParameterSchema(parameter, true, false);

        expect(schema).to.have.property('description');
        expect(schema.description).to.equal('My Description');
      });

      it("should set required to false for a boolean type", function() {
        parameter.type = 'boolean';
        var schema = builder.buildParameterSchema(parameter, true, false);

        expect(schema).to.have.property('required');
        expect(schema.required).to.equal(false);
      });

      it("should set required to false if the parameter is nullable", function() {
        parameter.nullable = true;
        var schema = builder.buildParameterSchema(parameter, true, false);

        expect(schema).to.have.property('required');
        expect(schema.required).to.equal(false);
      });

      it("should set required to true if the parameter is not nullable", function() {
        parameter.nullable = false;
        var schema = builder.buildParameterSchema(parameter, true, false);

        expect(schema).to.have.property('required');
        expect(schema.required).to.equal(true);
      });

      it("should generate a default if no default has been generated yet", function() {
        parameter.default = "myDefault";
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('default');
        expect(schema.default).to.equal('myDefault');
      });

      it("should not generate a default if the default has already been generated", function() {
        parameter.default = "myDefault";
        var schema = builder.buildParameterSchema(parameter, true, false);

        expect(schema).to.not.have.property('default');
      });

      it('should not setup a description if the parameter is part of an array', function() {
        parameter.description = 'My Description';
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema).to.not.have.property('description');
      });

      it('should not setup a title if the parameter is part of an array', function() {
        parameter.display_name = 'My Display Name';
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema).to.not.have.property('title');
      });

      it('should set a maximum for integer parameters with maximum specified', function() {
        parameter.type = 'Integer';
        parameter.maximum = 10;
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema.maximum).to.equal(10);
        expect(schema).to.not.have.property('maxLength');
        expect(schema).to.not.have.property('maxProperties');
      });

      it('should set a minimum for integer parameters with minimum specified', function() {
        parameter.type = 'Integer';
        parameter.minimum = 10;
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema.minimum).to.equal(10);
        expect(schema).to.not.have.property('minLength');
        expect(schema).to.not.have.property('minProperties');
      });

      it('should set a length maximum for string parameters with maximum specified', function() {
        parameter.type = 'String';
        parameter.maximum = 10;
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema.maxLength).to.equal(10);
        expect(schema).to.not.have.property('maximum');
        expect(schema).to.not.have.property('maxProperties');
      });

      it('should set a length minimum for string parameters with minimum specified', function() {
        parameter.type = 'String';
        parameter.minimum = 10;
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema.minLength).to.equal(10);
        expect(schema).to.not.have.property('minimum');
        expect(schema).to.not.have.property('minProperties');
      });

      it('should set a count maximum for dictionary parameters with maximum specified', function() {
        parameter.type = 'Dictionary';
        parameter.maximum = 10;
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema.maxProperties).to.equal(10);
        expect(schema).to.not.have.property('maximum');
        expect(schema).to.not.have.property('maxLength');
      });

      it('should set a count minimum for dictionary parameters with minimum specified', function() {
        parameter.type = 'Dictionary';
        parameter.minimum = 10;
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema.minProperties).to.equal(10);
        expect(schema).to.not.have.property('minimum');
        expect(schema).to.not.have.property('minLength');
      });

      it('should work with integer minimum and maximum', function() {
        parameter.type = 'Integer';
        parameter.minimum = 1;
        parameter.maximum = 10;
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema.minimum).to.equal(1);
        expect(schema.maximum).to.equal(10);
      });

      it('should work with string minimum and maximum', function() {
        parameter.type = 'String';
        parameter.minimum = 1;
        parameter.maximum = 10;
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema.minLength).to.equal(1);
        expect(schema.maxLength).to.equal(10);
      });

      it('should work with dictionary minimum and maximum', function() {
        parameter.type = 'Dictionary';
        parameter.minimum = 1;
        parameter.maximum = 10;
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema.minProperties).to.equal(1);
        expect(schema.maxProperties).to.equal(10);
      });

      it('should set a pattern for parameters with a regex', function() {
        parameter.type = 'String';
        parameter.regex = '.*';
        var schema = builder.buildParameterSchema(parameter, true, true);

        expect(schema.pattern).to.equal('.*');
      });

      describe("correctType", function() {
        it("should set the type of a simple any correctly", function() {
          parameter.type = 'Any';
          var schema    = builder.buildParameterSchema(parameter, true, false);

          expect(schema).to.have.property('type');
          expect(schema.type).to.equal('raw');
        });

        it("should set the type of a simple string correctly", function() {
          parameter.type = 'String';
          var schema    = builder.buildParameterSchema(parameter, true, false);

          expect(schema).to.have.property('type');
          expect(schema.type).to.equal('string');
        });

        it("should set the type of a simple integer correctly", function() {
          parameter.type = 'Integer';
          var schema    = builder.buildParameterSchema(parameter, true, false);

          expect(schema).to.have.property('type');
          expect(schema.type).to.equal('integer');
        });

        it("should set the type of a simple float correctly", function() {
          parameter.type = 'Float';
          var schema    = builder.buildParameterSchema(parameter, true, false);

          expect(schema).to.have.property('type');
          expect(schema.type).to.equal('number');
        });

        it("should set the type of a simple boolean correctly", function() {
          parameter.type = 'Boolean';
          var schema    = builder.buildParameterSchema(parameter, true, false);

          expect(schema).to.have.property('type');
          expect(schema.type).to.equal('boolean');
        });

        it("should set the type of a simple dictionary correctly", function() {
          parameter.type = 'Dictionary';
          var schema    = builder.buildParameterSchema(parameter, true, false);

          expect(schema).to.have.property('type');
          expect(schema.type).to.equal('object');
        });

        it("should set the type of a simple unknown type correctly", function() {
          parameter.type = 'Bad Type';
          var schema    = builder.buildParameterSchema(parameter, true, false);

          expect(schema).to.have.property('type');
          expect(schema.type).to.equal('string');
        });
      }); // End Describe correctType
    }); // End Describe buildSimpleParameterSchema

    describe("buildArrayParameterSchema", function() {

      beforeEach(function() {
        parameter.multi = true;
      });

      it('should set the title correctly', function() {
        parameter.display_name = 'My Display Name';

        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('title');
        expect(schema.title).to.equal('My Display Name');

      });

      it('should set the description correctly', function() {
        parameter.description = 'My Description';

        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('description');
        expect(schema.description).to.equal('My Description');
      });

      it('should set the type to array', function() {
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('type');
        expect(schema.type).to.equal('array');
      });

      it('should not generate a default if one has already been generated', function() {
        parameter.default = [1,2,3];
        var schema = builder.buildParameterSchema(parameter, true, false);

        expect(schema).to.not.have.property('default');
      });

      it('should generate an empty array if a default has not been genereated and the default is null', function() {
        parameter.default = null;
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('default');
        expect(schema.default).to.deep.equal([]);
      });

      it("should generate a valid array if a default has not been generated and the default is not null", function() {
        parameter.default = [1,2,3];
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('default');
        expect(schema.default).to.deep.equal([1,2,3]);
      });

      it("should setup the items property correctly", function() {
        parameter.type = 'string';
        parameter.default = ['a','b','c'];
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('items');
        expect(schema.items).to.have.property('type');
        expect(schema.items.type).to.equal('string');
      });
    }); // End Describe buildArrayParameterSchema

    describe("buildDictionaryParameterSchema", function() {

      var nestedParameter1;

      beforeEach(function() {
        nestedParameter1 = sinon.spy();
        nestedParameter1.type = 'Any';
        nestedParameter1.key  = "nestedParameter1";
        parameter.type = 'Dictionary';
        parameter.parameters = [nestedParameter1]
      });

      it("should set the format to raw if no parameters are defined", function() {
        parameter.parameters = undefined;
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('format');
        expect(schema.format).to.equal('raw');
      });

      it("should set the type to object", function() {
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('type');
        expect(schema.type).to.equal('object');
      });

      it('should set the title if it is not part of an array', function() {
        parameter.display_name = 'My Display Name';
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('title');
        expect(schema.title).to.equal('My Display Name');
      });

      it('should not set the title if it is part of an array', function() {
        parameter.display_name = 'My Display Name';
        var schema = builder.buildParameterSchema(parameter, false, true);

        expect(schema).to.not.have.property('title');
      });

      it("should set the description if it is not part of an array", function() {
        parameter.description = 'My Description';
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('description');
        expect(schema.description).to.equal('My Description');
      });

      it('should not set the description if it is part of an array', function() {
        parameter.display_name = 'My Description';
        var schema = builder.buildParameterSchema(parameter, false, true);

        expect(schema).to.not.have.property('description');
      });

      it('should not attempt to set the default if has already been set', function() {
        var schema = builder.buildParameterSchema(parameter, true, false);

        expect(schema).to.not.have.property('default');
      });

      it('should set the default to an empty dictionary if it has not already been set and it is null', function() {
        parameter.default = null;
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('default');
        expect(schema.default).to.deep.equal({nestedParameter1: null});
      });

      it('should set up a properties value correctly', function() {
        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('properties');

        var properties = schema.properties;
        expect(properties).to.have.property('nestedParameter1')
      });

      it("should use the default of nested parameters if no default has been set and there is no default defined", function() {
        nestedParameter1.default = "myDefault";
        parameter.default = null;

        var schema = builder.buildParameterSchema(parameter, false, false);

        expect(schema).to.have.property('default');
        expect(schema.default).to.deep.equal({nestedParameter1: 'myDefault'});

        expect(schema.properties.nestedParameter1).to.not.have.property('default');
      });
    }); // End Describe buildDictionaryParameterSchema
  }); // End Describe buildParameterSchema
});
