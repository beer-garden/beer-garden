xdescribe("FormBuilder", function() {

  var sandbox, builder;

  beforeEach(module('bgApp'));

  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function(_FormBuilder_) {
    builder = _FormBuilder_
  }));

  describe("build", function() {

    var system, command;

    beforeEach(function() {
      system  = sinon.spy();
      command = sinon.spy();
    });

    it("should build both the command and system field sets", function() {
      buildCommandFieldSet = sandbox.stub(builder, 'buildCommandFieldSet');
      buildSystemFieldSet = sandbox.stub(builder, 'buildSystemFieldSet');

      var form = builder.build(system, command);
      expect(buildCommandFieldSet).to.have.been.called;
      expect(buildSystemFieldSet).to.have.been.called;
    });

    describe("buildSystemFieldSet", function() {

      xit("should generate an enabled submit button after the comment field if the system is running", function() {
        system.status = 'RUNNING';
        var form = builder.build(system, command);
        expect(form[3]).to.deep.equal({ 'type' : 'submit', 'style' : 'btn-primary', 'fieldHtmlClass' : 'btn-block',
          'title' : 'Make Request', 'readonly': false });
      });

      xit("should generate a disabled submit button after the comment field if the system is not running", function() {
        system.status = 'STOPPED';
        var form = builder.build(system, command);
        expect(form[3]).to.deep.equal({ 'type' : 'submit', 'style' : 'btn-primary', 'fieldHtmlClass' : 'btn-block',
          'title' : 'Make Request', 'readonly': true });
      });

      xit("should setup the sectionField of the defaultForm up correctly", function() {
        var form = builder.build(system, command);
        var fieldset = form[0];
        var fieldsetItems = fieldset['items'];
        var sectionField  = fieldsetItems[0];

        expect(sectionField).to.have.property('type');
        expect(sectionField).to.have.property('htmlClass');
        expect(sectionField).to.have.property('items');

        expect(sectionField['type']).to.equal('section');
        expect(sectionField['htmlClass']).to.equal('row');
        expect(sectionField['items'].length).to.equal(2);
      });

      xit("should setup the items of the section field correctly", function() {
        var form = builder.build(system, command);
        var fieldset = form[0];
        var fieldsetItems = fieldset['items']
        var sectionField  = fieldsetItems[0];
        var item1         = sectionField['items'][0]
        var item2         = sectionField['items'][1]

        expect(item1).to.have.property('type');
        expect(item1).to.have.property('htmlClass');
        expect(item1).to.have.property('items');

        expect(item2).to.have.property('type');
        expect(item2).to.have.property('htmlClass');
        expect(item2).to.have.property('items');

        expect(item1['type']).to.equal('section');
        expect(item1['htmlClass']).to.equal('col-md-6');
        expect(item1['items'].length).to.equal(1);

        expect(item2['type']).to.equal('section');
        expect(item2['htmlClass']).to.equal('col-md-6');
        expect(item2['items'].length).to.equal(1);
      });

      xit("should setup the systemItem correctly", function() {
        var fieldset = builder.buildSystemFieldSet(system, command);
        var fieldsetItems = fieldset['items']
        var sectionField  = fieldsetItems[0];
        var item1         = sectionField['items'][0]
        var systemItem    = item1['items'][0]

        expect(systemItem).to.have.property('key');
        expect(systemItem).to.have.property('feedback');
        expect(systemItem).to.have.property('disableSuccessState');
        expect(systemItem).to.have.property('disableErrorState');
        expect(systemItem).to.have.property('readonly');
        expect(systemItem).to.have.property('required');

        expect(systemItem['key']).to.equal('system');
        expect(systemItem['feedback']).to.equal(false);
        expect(systemItem['disableSuccessState']).to.equal(true);
        expect(systemItem['disableErrorState']).to.equal(true);
        expect(systemItem['readonly']).to.equal(true);
        expect(systemItem['required']).to.equal(true);
      });

      xit("should setup the commandItem correctly", function() {
        var form = builder.build(system, command);
        var fieldset = form[0];
        var fieldsetItems = fieldset['items']
        var sectionField  = fieldsetItems[0];
        var item2         = sectionField['items'][1]
        var commandItem   = item2['items'][0]

        expect(commandItem).to.have.property('key');
        expect(commandItem).to.have.property('feedback');
        expect(commandItem).to.have.property('disableSuccessState');
        expect(commandItem).to.have.property('disableErrorState');
        expect(commandItem).to.have.property('readonly');
        expect(commandItem).to.have.property('required');

        expect(commandItem['key']).to.equal('command');
        expect(commandItem['feedback']).to.equal(false);
        expect(commandItem['disableSuccessState']).to.equal(true);
        expect(commandItem['disableErrorState']).to.equal(true);
        expect(commandItem['readonly']).to.equal(true);
        expect(commandItem['required']).to.equal(true);
      });

      xit('should generate add an object to the default if the system has an instance name', function() {
        system.instance_names = ['instance1'];
        var form = builder.build(system, command);
        var fieldset = form[0];
        var fieldsetItems = fieldset['items'];
        expect(fieldsetItems.length).to.equal(2);

        var instanceNameField = fieldsetItems[1];
        expect(instanceNameField).to.have.property('key');
        expect(instanceNameField).to.have.property('feedback');

        expect(instanceNameField['key']).to.equal('instance_name');
        expect(instanceNameField['feedback']).to.equal(false);
      });
    }); // End Describe buildSystemFieldSet

    describe("buildCommandFieldSet", function() {

      var parameter;

      beforeEach(function() {
        parameter = { key: 'param1', optional: true, multi: false, type: 'string' };
      });

      it("should setup a tabular view if there are required and optional parameters", function() {
        command.parameters = [parameter];

        var fieldset = builder.buildCommandFieldSet(command);
        expect(fieldset.items.length).to.equal(1);

        var tabs = fieldset.items[0];
        expect(tabs).to.have.property('type');
        expect(tabs).to.have.property('tabs');

        expect(tabs.type).to.equal('tabs');
        expect(tabs.tabs.length).to.equal(2);
      });

      it("should generate the required items correctly", function() {
        command.parameters = [parameter];

        var fieldset = builder.buildCommandFieldSet(command);
        var tabs        = fieldset.items[0];
        var requiredTab = tabs.tabs[0];

        expect(requiredTab).to.have.property('title');
        expect(requiredTab).to.have.property('items');

        expect(requiredTab['title']).to.equal('Required Fields');
        expect(requiredTab['items'].length).to.equal(1)
      });

      it("should generate the optional items correctly", function() {
        command.parameters = [parameter];

        var fieldset = builder.buildCommandFieldSet(command);
        var tabs        = fieldset.items[0];
        var optionalTab = tabs.tabs[1];

        expect(optionalTab).to.have.property('title');
        expect(optionalTab).to.have.property('items');

        expect(optionalTab['title']).to.equal('Optional Fields');
        expect(optionalTab['items'].length).to.equal(1);
      });

      it("should setup the individual parameter form value correctly", function() {
        parameter['optional'] = false;
        command.parameters = [parameter];

        var fieldset = builder.buildCommandFieldSet(command);
        var fieldsetItems = fieldset['items'];
        var tabs = fieldsetItems[0]['tabs'];
        var parameterFormItem = tabs[0]['items'][0];
        // var parameterFormItem = fieldsetItems[1];

        expect(parameterFormItem).to.have.property('key');
        expect(parameterFormItem['key']).to.equal('parameters.param1');
      });

      it("should set startEmpty to true if it is a multi parameter that is optional", function() {
        parameter['multi'] = true
        command.parameters = [parameter];

        var fieldset = builder.buildCommandFieldSet(command);
        var fieldsetItems = fieldset['items'];
        var tabs = fieldsetItems[0]['tabs'];
        var item = tabs[1]['items'][0];

        expect(item).to.have.property('startEmpty');
        expect(item['startEmpty']).to.equal(true);
      });
    }); // End Describe buildCommandFieldSet
  }); // End Describe build

  describe("reset", function() {

    var form, model, system, command, fullCommand, parameter;

    beforeEach(function() {
      form            = { $setPristine: sandbox.stub() };
      model           = {};
      system          = { name: 'systemName', version: '1.0.0', instances: [{name: 'default'}] };
      command         = { name: 'commandName' };
      parameter       = { default : 'bar', type: "string", multi: false, nullable: false,
                          key: 'foo' }
      fullCommand     = { parameters: [parameter] }
    });

    describe("model values", function() {

      it("should delete all the existing keys from the model", function() {
        model = {'foo':'bar', 'baz' : 'bat'}
        builder.reset(form, model, system, command);
        expect(model).to.not.have.property('foo');
        expect(model).to.not.have.property('baz');
      });

      if('should add the correct values to the model', function() {
        builder.reset(form, model, system, command);
        expect(model).to.have.property('system');
        expect(model['system']).to.equal('systemName');
        expect(model).to.have.property('system_version');
        expect(model['system_version']).to.equal('1.0.0');
        expect(model).to.have.property('command');
        expect(model['command']).to.equal('commandName');
        expect(model).to.have.property('instance_name');
        expect(model['instance_name']).to.equal('default');
        expect(model).to.have.property('parameters');
        expect(model['parameters']).to.deep.equal({});
        expect(model).to.have.property('comment');
        expect(model['comment']).to.equal('');
      });

      it('should not set an instance default if more than one', function() {
        system.instances.push({name: 'default2'})
        builder.reset(form, model, system, command);
        expect(model).to.not.have.property('instance_name');
      });

      it('should call $setPristine on the form', function() {
        builder.reset(form, model, system, command);
        sinon.assert.calledOnce(form.$setPristine)
      });

      it('should not setup any defaults if the parameter has an undefined default', function() {
        delete parameter.default;
        builder.reset(form, model, system, fullCommand)
        expect(model).to.have.property('parameters');
        expect(model['parameters']).to.deep.equal({});
      });

      it('should not set a default parameter if the default is null and nullable is false', function() {
        parameter.default = null;
        builder.reset(form, model, system, fullCommand)
        expect(model).to.have.property('parameters');
        expect(model['parameters']).to.deep.equal({});
      });

      it('should set a default parameter if the default is null and nullable is true', function() {
        parameter.default = null;
        parameter.nullable = true;
        builder.reset(form, model, system, fullCommand)
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.deep.equal(null);
      });

      it('should set a default parameter if the default is not null but nullable is still true', function() {
        parameter.nullable = true;
        builder.reset(form, model, system, fullCommand)
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.deep.equal('bar');
      });

      it('should set a default parameter if the default is not null', function() {
        builder.reset(form, model, system, fullCommand)
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.deep.equal('bar');
      });

      it('should set a booleans default parameter to false if it is null', function() {
        parameter.type = 'boolean';
        parameter.default = null;
        builder.reset(form, model, system, fullCommand)
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.deep.equal(false);
      });

      it("should set a booleans default parameter to null if it is nullable", function() {
        parameter.type = 'boolean';
        parameter.default = null;
        parameter.nullable = true;
        builder.reset(form, model, system, fullCommand)
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.deep.equal(null);
      });

      it('should set an arrays default parameter to an empty array if it is null', function() {
        parameter.multi = true;
        parameter.default = null;
        builder.reset(form, model, system, fullCommand)
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.deep.equal([]);
      });

      it('should set an arrays default parameter up correctly and extend it correctly', function() {
        parameter.multi = true;
        parameter.default = ['a','b','c'];
        builder.reset(form, model, system, fullCommand)
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.deep.equal(['a','b','c']);
        // Make sure that the default is not the same object as what is in the model now.
        // This is important because we don't want modifications by the user to modify the
        // default specified by the plugin developer
        expect(model['parameters']['foo']).to.not.equal(parameter.default);
      });

      it('should set a dictionary\'s default parameter to an empty dictionary if it is null', function() {
        parameter.type    = 'dictionary';
        parameter.default = null;
        builder.reset(form, model, system, fullCommand)
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.deep.equal({});
      });

      it('should set a dictionary\'s default parameter up correctly and extend it correctly', function() {
        parameter.type    = 'dictionary';
        parameter.default = {'key' : 'value'};
        builder.reset(form, model, system, fullCommand)
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.deep.equal({'key':'value'});
        // Make sure that the default is not the same object as what is in the model now.
        // This is important because we don't want modifications by the user to modify the
        // default specified by the plugin developer
        expect(model['parameters']['foo']).to.not.equal(parameter.default);
      });

      it('should not generate defaults for dictionary\'s which are nullable but have defaults in models', function() {
        parameter.type = 'dictionary';
        parameter.default = null;
        parameter.nullable = true;
        parameter.parameters = [{type: "string", default: "foo"}]
        builder.reset(form, model, system, fullCommand)
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.deep.equal({});
      });

      it('should correctly set a boolean\'s default to false if it is defined that way', function() {
        parameter.type = 'boolean';
        parameter.default = false;
        builder.reset(form, model, system, fullCommand);
        expect(model['parameters']).to.have.property('foo');
        expect(model['parameters']['foo']).to.equal(false);
      });
    }); // End Describe Model Value

    describe("View Value", function() {

      var fakeModel;

      beforeEach(function() {
        fakeModel = { $setViewValue: sandbox.stub(), $render: sandbox.stub() };
        form = { $setPristine: sandbox.stub(), 'foo': fakeModel };
      });

      it("should call setViewValue", function() {
        builder.reset(form, model, system, fullCommand);
        sinon.assert.calledOnce(fakeModel.$setViewValue);
      });

      it("should call Render", function() {
        builder.reset(form, model, system, fullCommand);
        sinon.assert.calledOnce(fakeModel.$render);
        sinon.assert.calledWithExactly(fakeModel.$render);
      });

      it("should setup the ViewValue for booleans correctly", function() {
        parameter.type = 'boolean';
        parameter.default = true;
        builder.reset(form, model, system, fullCommand);
        sinon.assert.calledOnce(fakeModel.$setViewValue);
        sinon.assert.calledWithExactly(fakeModel.$setViewValue, true);
      });

      it('should setup the ViewValue for non-objects correctly', function() {
        builder.reset(form, model, system, fullCommand);
        sinon.assert.calledOnce(fakeModel.$setViewValue);
        sinon.assert.calledWithExactly(fakeModel.$setViewValue, 'bar');
      });

      it('should setup the ViewValue for nulls correctly', function() {
        parameter.default = null;
        builder.reset(form, model, system, fullCommand);
        sinon.assert.calledOnce(fakeModel.$setViewValue);
        sinon.assert.calledWithExactly(fakeModel.$setViewValue, null);
      });

      it('should setup the ViewValue for arrays correctly', function() {
        parameter.multi   = true;
        parameter.default = ['a','b','c'];
        builder.reset(form, model, system, fullCommand);
        sinon.assert.calledOnce(fakeModel.$setViewValue);
        sinon.assert.calledWithExactly(fakeModel.$setViewValue, '[\"a\",\"b\",\"c\"]');
      });

      it('should setup the ViewValue for objects correctly', function() {
        parameter.type    = 'dictionary';
        parameter.default = {"foo":"bar"};
        builder.reset(form, model, system, fullCommand);
        sinon.assert.calledOnce(fakeModel.$setViewValue);
        sinon.assert.calledWithExactly(fakeModel.$setViewValue, JSON.stringify({"foo":"bar"}));
      });
    }); // End Describe View Value
  }); // End Describe Reset
});
