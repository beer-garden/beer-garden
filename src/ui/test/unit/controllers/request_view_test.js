describe("RequestViewController", function() {

  var sandbox, deferredGet, MockRequestService,
      $stateParams, $timeout, $animate, $state, $scope;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));

  beforeEach(module(function($provide) {
    $provide.decorator('$timeout', function($delegate) {
      return sinon.spy($delegate);
    });
  }));

  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function($rootScope, $controller, _$state_, _$stateParams_,
                             _$timeout_, _$animate_, _$q_, _RequestService_) {

    $scope             = $rootScope.$new();
    $state             = _$state_;
    $timeout           = _$timeout_;
    $animate           = _$animate_;
    $stateParams       = _$stateParams_;
    $stateParams.request_id = 'requestId';

    deferredGet        = _$q_.defer();
    MockRequestService = sandbox.stub(_RequestService_);
    MockRequestService.getRequest.returns(deferredGet.promise);

    $controller('RequestViewController', {$scope: $scope, $stateParams: $stateParams, $timeout: $timeout,
                                          $animate: $animate, RequestService: MockRequestService});
  }));

  describe("init", function() {

    it("should call getRequest", function() {
      expect(MockRequestService.getRequest).to.have.been.calledWithExactly('requestId');
    });

  });

  describe("successCallback", function() {

    beforeEach(function() {
      sinon.stub($scope, 'formatOutput');
      sinon.stub($scope, 'formatDate');
    });

    it("should set some scope properties", function() {
      var response = { data: { status: 'SUCCESS' } };
      $scope.successCallback(response);
      expect($scope.request.data).to.deep.equal(response.data);
      expect($scope.request.loaded).to.be.true;
      expect($scope.request.error).to.be.false;
    });

    it("should update scope children based on children view expanded status", function() {
      var response = {
        data: { status: 'SUCCESS', children: [{command: 'test'}] }
      };

      $scope.children_collapsed = false;
      $scope.children = [];
      $scope.successCallback(response);
      expect($scope.children).to.deep.equal(response.data.children);

      $scope.children_collapsed = true;
      $scope.children = [];
      $scope.successCallback(response);
      expect($scope.children).to.deep.equal([]);
    });

    it("should not make another request if the request is finished", function() {
      MockRequestService.getRequest.reset();

      $scope.successCallback({ data: { status: "SUCCESS" } });
      $scope.successCallback({ data: { status: "ERROR" } });
      $timeout.flush();
      $timeout.verifyNoPendingTasks();
      expect($scope.timeoutRequest).to.be.undefined;
      expect(MockRequestService.getRequest).to.not.be.called;
    });

    it("should make another request if the request isn't finished", function() {
      MockRequestService.getRequest.reset();

      $scope.successCallback({ data: { status: "IN PROGRESS" } });
      $timeout.flush()
      $timeout.verifyNoPendingTasks();
      expect(MockRequestService.getRequest).to.be.called;
    });

  }); // End describe successCallback

  describe("failureCallback", function() {

    it("should set some scope properties", function() {
      $scope.failureCallback({ data: { message: 'something is broken' } });
      expect($scope.request.loaded).to.be.false;
      expect($scope.request.error).to.be.true;
      expect($scope.request.errorMessage).to.equal('something is broken');
    });

  }); // End describe failureCallback

  describe("hasParent", function() {

    it("should return false with no parent", function() {
      request = {};
      expect($scope.hasParent(request)).to.be.false;
    });

    it("should return false with a null parent", function() {
      request = {parent: null};
      expect($scope.hasParent(request)).to.be.false;
    });

    it("should return true with a parent", function() {
      request = {parent: 'parent'};
      expect($scope.hasParent(request)).to.be.true;
    });

  }); // End describe hasParent

  describe("hasChildren", function() {

    it("should return false with no children", function() {
      request = {};
      expect($scope.hasChildren(request)).to.be.false;
    });

    it("should return false with null children", function() {
      request = {children: null};
      expect($scope.hasChildren(request)).to.be.false;
    });

    it("should return false with empty children array", function() {
      request = {children: []};
      expect($scope.hasChildren(request)).to.be.false;
    });

    it("should return true with children", function() {
      request = {children: ['child']};
      expect($scope.hasChildren(request)).to.be.true;
    });

  }); // End describe hasChildren

  describe("toggleChildren", function() {

    it("should toggle the boolean scope variable", function() {
      $scope.children_collapsed = false;

      $scope.toggleChildren();
      expect($scope.children_collapsed).to.be.true;
    });

    it("should correctly set the scope array", function() {
      $scope.children_collapsed = true;
      $scope.children = [];
      $scope.request.data = {children: [{command: 'say'}]};

      $scope.toggleChildren();
      expect($scope.children).to.deep.equal([{command: 'say'}]);
    });

    it("should correctly unset the scope array", function() {
      $scope.children_collapsed = false;
      $scope.children = [{command: 'say'}];
      $scope.request.data = {children: [{command: 'say'}]};

      $scope.toggleChildren();
      expect($scope.children).to.deep.equal([]);
    });

    it("should enable animation on the table, then disable it after some amount of time", function() {
      $scope.children_collapsed = false;
      $animate.enabled = sinon.spy();

      $scope.toggleChildren();
      expect($animate.enabled).to.be.calledOnce;
      expect($animate.enabled).to.be.calledWith(sinon.match.any, true);

      $timeout.flush();
      expect($animate.enabled).to.be.calledTwice;
      expect($animate.enabled).to.be.calledWith(sinon.match.any, false);
      $timeout.verifyNoPendingTasks();
    });

  });

  describe("instanceColumn", function() {

    describe("instanceColumn", function() {

      it("should be false when request has no instance and no children", function() {
        $scope.request.data = {};
        expect($scope.showColumn('instance_name')).to.be.false;
      });

      it("should be false when request has no instance and children have no instances", function() {
        $scope.request.data = {children: []};
        expect($scope.showColumn('instance_name')).to.be.false;
      });

      it("should be true when request has an instance", function() {
        $scope.request.data = {instance_name: 'instance1'};
        expect($scope.showColumn('instance_name')).to.be.true;
      });

      it("should be true when a child has an instance", function() {
        $scope.request.data = {
          children: [{instance_name: 'child_instance'}]
        };
        expect($scope.showColumn('instance_name')).to.be.true;
      });

      it("should be true when request and a child has an instance", function() {
        $scope.request.data = {
          instance_name: 'instance1',
          children: [{instance_name: 'child_instance'}]
        };
        expect($scope.showColumn('instance_name')).to.be.true;
      });

    });

    describe("errorTypeColumn", function() {

      it("should be false when request has no error and no children", function() {
        $scope.request.data = {};
        expect($scope.showColumn('error_class')).to.be.false;
      });

      it("should be false when request has no error and children have no errors", function() {
        $scope.request.data = {children: []};
        expect($scope.showColumn('error_class')).to.be.false;
      });

      it("should be true when request has an error", function() {
        $scope.request.data = {error_class: 'ValueError'};
        expect($scope.showColumn('error_class')).to.be.true;
      });

      it("should be true when a child has an error", function() {
        $scope.request.data = {
          children: [{error_class: 'ValueError'}]
        };
        expect($scope.showColumn('error_class')).to.be.true;
      });

      it("should be true when request and a child has an error", function() {
        $scope.request.data = {
          error_class: 'ValueError',
          children: [{error_class: 'OtherError'}]
        };
        expect($scope.showColumn('error_class')).to.be.true;
      });

    });

  });

  describe("countNodes", function() {

    it("should return 1 for null or undefined values", function() {
      expect($scope.countNodes(null)).to.equal(1);
    });

    it("should return 1 for non-object, non-array values", function() {
      expect($scope.countNodes("Hello there, world")).to.equal(1);
    });

    it("should return 1 for an empty object", function() {
      expect($scope.countNodes({})).to.equal(1);
    });

    it("should correctly count object nodes", function() {
      var input = {"key": "value"};
      expect($scope.countNodes(input)).to.equal(2);
    });

    it("should correctly count nested object nodes", function() {
      var input = {"key": {"nested": "value"}};
      expect($scope.countNodes(input)).to.equal(3);
    });

    it("should return 1 for an empty array", function() {
      expect($scope.countNodes([])).to.equal(1);
    });

    it("should correctly count array nodes", function() {
      var input = ['val1', 'val2'];
      expect($scope.countNodes(input)).to.equal(3);
    });

    it("should correctly count nested array nodes", function() {
      var input = {"key": ['val1', 'val2']};
      expect($scope.countNodes(input)).to.equal(4);
    });

  }); // End describe countNodes

  describe("formatOutput", function() {

    beforeEach(function() {
      $scope.request = sinon.stub();
      $scope.request.data = sinon.stub();
    });

    it("should produce 'null' raw_output when null", function() {
      $scope.request.data.output = null;

      $scope.formatOutput();
      expect($scope.raw_output).to.equal('null');
    });

    describe("JSON output", function() {

      beforeEach(function() {
        $scope.request.data.output_type = 'JSON';
        $scope.request.data.output = '{"key": "value"}';
      });

      it("should fail for unparsable JSON, fallback to raw string", function() {
        sinon.stub($scope, 'stringify').throws();

        $scope.formatOutput();
        expect($scope.raw_output).to.equal($scope.request.data.output);
        expect($scope.formatted_available).to.be.false;
        expect($scope.show_formatted).to.be.false;
        expect($scope.format_error_title).to.exist;
        expect($scope.format_error_msg).to.exist;
      });

      it("should set flags and data correctly for small JSON", function() {
        $scope.formatOutput();
        expect($scope.formatted_output).to.exist;
        expect($scope.raw_output).to.not.equal($scope.request.data.output);
        expect($scope.formatted_available).to.be.true;
        expect($scope.show_formatted).to.be.true
        expect($scope.format_error_title).to.be.undefined;
        expect($scope.format_error_msg).to.be.undefined;
      });

      it("should set flags and data correctly for big JSON", function() {
        sinon.stub($scope, 'countNodes', function() {return 2000;})

        $scope.formatOutput();
        expect($scope.formatted_output).to.exist;
        expect($scope.raw_output).to.not.equal($scope.request.data.output);
        expect($scope.formatted_available).to.be.false;
        expect($scope.show_formatted).to.be.false;
        expect($scope.format_error_title).to.exist;
        expect($scope.format_error_msg).to.exist;
      });

    });

    it("should format STRING output as JSON if parsable", function() {
      $scope.request.data.output_type = 'STRING';
      $scope.request.data.output = '{"key": "value"}';

      $scope.formatOutput();
      expect($scope.raw_output).to.not.equal($scope.request.data.output);
    });

    it("should format as the original STRING if unparsable", function() {
      $scope.request.data.output_type = 'STRING';
      $scope.request.data.output = 'this is not json';

      $scope.formatOutput();
      expect($scope.raw_output).to.equal($scope.request.data.output);
    });

  }); // End describe formatOutput

  describe("canRepeat", function() {

    it('should return false by default', function() {
      expect($scope.canRepeat({})).to.be.false;
    });

    it('should return true if the request status is SUCCESS', function() {
      expect($scope.canRepeat({ status: 'SUCCESS'})).to.be.true;
    });

    it('should return true if the request status is ERROR', function() {
      expect($scope.canRepeat({ status: 'ERROR'})).to.be.true;
    });

    it('should return true if the request status is CANCELED', function() {
      expect($scope.canRepeat({ status: 'CANCELED'})).to.be.true;
    });

  }) // End Describe canRepeat

  describe("$destroy", function() {

    it("should do nothing if there is no timeoutRequest", function() {
      $timeout.cancel = sinon.spy();
      $scope.$broadcast('$destroy');
      sinon.assert.notCalled($timeout.cancel);
    });

    it("should cancel any requests if destroy is called", function() {
      $scope.timeoutRequest = sinon.spy();
      $timeout.cancel = sinon.spy();
      $scope.$broadcast("$destroy");
      sinon.assert.calledOnce($timeout.cancel);
      sinon.assert.calledWith($timeout.cancel, $scope.timeoutRequest);
    });

  }); // End Describe $destroy

  describe("redoRequest", function() {

    it("should call getCommandId with the correct information", function() {
      var request = {};
      var thenF = sinon.spy();
      MockRequestService.getCommandId.returns({then: function(s,e) {thenF()}});

      $scope.redoRequest(request);
      expect(MockRequestService.getCommandId).to.have.been.calledOnce;
      expect(MockRequestService.getCommandId).to.have.been.calledWith(request);
    });

    it("should alert if a server error occurs when getting the Command ID", function() {
      var request = {};
      var stub = sandbox.stub(window, 'alert');
      MockRequestService.getCommandId.returns({then:
        function(s,e) {
          e(null);
        }
      });

      $scope.redoRequest(request);
      expect(stub).to.have.been.calledOnce;
    });

    it('should alert if the commandId is null', function() {
      var request = { system: 'systemName'};
      var data = null;
      var stub = sandbox.stub(window, 'alert');
      MockRequestService.getCommandId.returns({then:
        function(s,e) {
          s(data);
        }
      });

      $scope.redoRequest(request);
      expect(stub).to.have.been.calledOnce;
    });

    it('should call $state.go correctly with the correct information', function() {
      var goStub = sandbox.stub($state, 'go');
      var request = {
        system : 'systemName',
        system_version: '1.0.0',
        instance_name: 'default',
        command: 'commandName',
        comment: '',
        parameters: {}
      }
      var data = 'id';
      MockRequestService.getCommandId.returns({then:
        function(s,e) {
          s(data);
        }
      });

      $scope.redoRequest(request);
      expect(goStub).to.have.been.calledOnce;
      expect(goStub).to.have.been.calledWith('command', { command_id: 'id', request: request });
    });
  });

}); // End Describe RequestViewController
