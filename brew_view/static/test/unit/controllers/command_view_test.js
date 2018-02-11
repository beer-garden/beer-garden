describe("CommandViewController", function() {

  var sandbox, command, schema, form, deferredCreate, deferredGetCommand, deferredGetSystem,
      $rootScope, $scope, $location, $stateParams, $q, $sce,
      MockCommandService, SpyRequestService, MockSystemService,
      MockSFBuilderService, MockUtilityService;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));
  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function(_$rootScope_, $controller, _$location_, _$stateParams_, _$q_, _$sce_, _CommandService_,
                             _RequestService_, _SystemService_, _SFBuilderService_, _UtilityService_) {

    schema                = {'schemaKey': 'schemaValue'};
    form                  = ['formValue1', 'formValue' ];
    command               = sinon.spy();
    command.system        = "http://localhost/api/v1/systems/systemId";
    $scope                = _$rootScope_.$new();
    $scope.config         = {'APPLICATION_NAME': "Beer Garden"};
    $scope.$broadcast     = sinon.spy();
    $location             = _$location_;
    $stateParams          = _$stateParams_;
    $stateParams.command_id = 'commandId';
    $q                    = _$q_;
    $sce                  = _$sce_;

    deferredCreate        = $q.defer();
    MockRequestService    = sandbox.stub(_RequestService_);
    MockRequestService.createRequest.returns(deferredCreate.promise);

    deferredGetSystem     = $q.defer();
    MockSystemService     = sandbox.stub(_SystemService_);
    MockSystemService.getSystem.returns(deferredGetSystem.promise);

    deferredGetCommand    = $q.defer();
    MockCommandService    = sandbox.stub(_CommandService_);
    MockCommandService.getCommand.returns(deferredGetCommand.promise);
    MockCommandService.findSystem.returns('system');

    MockSFBuilderService = sandbox.stub(_SFBuilderService_);
    MockSFBuilderService.build.returns({});

    $controller('CommandViewController', { $location: $location,
      $scope: $scope, $stateParams: $stateParams, $sce: $sce, CommandService: MockCommandService,
      RequestService: MockRequestService, SFBuilderService: MockSFBuilderService });
  }));

  describe("init", function() {

    it("should call getCommand on load", function() {
      expect(MockCommandService.getCommand).to.have.been.calledWithExactly('commandId');
    });

    it("should also request the System if the command has no template", function() {
      deferredGetCommand.resolve({ data: { system: {id: 'systemId'} }, status: 'SUCCESS' });
      $scope.$apply();
      expect(MockSystemService.getSystem).to.have.been.calledWithExactly('systemId', false);
      sinon.assert.calledWithMatch(MockSystemService.getSystem, 'systemId');
    });

    it("should just set the template if the command has one", function() {
      deferredGetCommand.resolve({ data: { template: '<div></div>' }, status: 'SUCCESS' });
      $scope.$apply();
      expect($scope.template).to.equal('<div></div>');
      expect(MockSystemService.getSystem).to.not.have.been.called;
    });

    it("should sanitize HTML by default", function() {
      var trust = sandbox.stub($sce, 'trustAsHtml');
      deferredGetCommand.resolve({ data: { template: '<div></div>' }, status: 'SUCCESS' });
      $scope.$apply();
      expect(trust).to.not.have.been.called;
    });

    it("should allow unsanitized HTML if configured to", function() {
      var trust = sandbox.stub($sce, 'trustAsHtml');
      $scope.config = {allow_unsafe_templates: true};
      deferredGetCommand.resolve({ data: { template: '<div></div>' }, status: 'SUCCESS' });
      $scope.$apply();
      expect(trust).to.have.been.called;
    });

  }); // End Describe Init

  describe('when submitting the form', function() {
    var form, model;

    beforeEach(function() {
      form = sinon.spy();
      model = sinon.spy();
    });

    describe('a valid submission', function() {

      beforeEach(function() {
        form.$valid = true;
      });

      it("should remove all the old alerts", function() {
        form.$error = {}
        $scope.alerts = ['alert1', 'alert2'];
        $scope.submitForm(form, model);
        expect($scope.alerts.length).to.equal(0)
      });

      it("should broadcast schemaFormValidate message", function() {
        $scope.submitForm(form, model);
        sinon.assert.calledWithExactly($scope.$broadcast, 'schemaFormValidate');
      });

      it("should correctly create a new request", function() {
        var real_system_name = 'system_name';
        var display_name = 'Display Name';

        $scope.system.name = real_system_name;
        $scope.system.display_name = display_name;
        model.system = display_name;

        $scope.submitForm(form, model);
        expect(model.system).to.equal(real_system_name);
        expect(model.metadata.system_display_name).to.equal(display_name);
        expect(MockRequestService.createRequest).to.have.been.calledWithExactly(model);
      });

      it("should update the location if createRequest succeeds", function() {
        $scope.submitForm(form, model);
        deferredCreate.resolve({ data: { id: 'requestId' } });

        $scope.$apply();
        expect($location.path()).to.be.equal('/requests/requestId');
      });

      it("should do error things if createRequest fails", function() {
        $scope.submitForm(form, model);
        deferredCreate.reject({ data: { message: 'No Bueno' } });

        $scope.$apply();
        expect($scope.createError).to.be.true;
        expect($scope.createErrorMessage).to.exist;
      });
    }); // End Describe Valid Submission

    describe("an invalid submission", function() {

      beforeEach(function() {
        form.$valid = false;
        form.$error = [{'key1' : {$name: 'param1'} }, {'key2' : {$name: 'param2'} }];
      });

      it("should remove all the old alerts", function() {
        $scope.alerts = ['alert1', 'alert2'];
        $scope.submitForm(form, model);
        expect($scope.alerts.length).to.equal(1);
        expect($scope.alerts).to.not.contain('alert1');
      });

      it("should create a new alert", function() {
        $scope.alerts = [];
        $scope.submitForm(form, model);
        expect($scope.alerts.length).to.equal(1);
      });
    }); // End Describe Invalid Submission

  }); // End Describe submitForm

  describe("reset", function() {
    var form, model, system, command;

    beforeEach(function() {
      form    = sinon.spy();
      model   = sinon.spy();
      system  = sinon.spy();
      command = sinon.spy();

      form.$setPristine = sinon.stub();
    });

    it("should clear out the alerts", function() {
      $scope.alerts = [1,2,3];
      $scope.reset(form, model, system, command);
      expect($scope.alerts.length).to.equal(0);
    });

    it('should set createError to false', function() {
      $scope.createError = true;
      $scope.reset(form, model, system, command);
      expect($scope.createError).to.equal(false);
    });

    it("should rebuild the schemaForm and set pristine", function() {
      $scope.baseModel = {'test': 'model'};
      $scope.reset(form, model, system, command);
      sinon.assert.calledOnce(MockSFBuilderService.build);
      sinon.assert.calledOnce(form.$setPristine);
    });

  }); // End Describe reset

  describe("closeAlert", function() {

    it("should remove an alert", function() {
      $scope.alerts = [1];
      $scope.closeAlert(0);
      expect($scope.alerts.length).to.equal(0);
    });

  }); // End Describe closeAlert

}); // End Describe CommandIndexController
