describe("SystemViewController", function() {

  var sandbox, $scope, $stateParams, $timeout, MockSystemService, MockCommandService;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));
  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(module(function($provide) {
    $provide.decorator('$timeout', function($delegate) {
      return sinon.spy($delegate);
    });
  }));

  beforeEach(inject(function($rootScope, $controller, _SystemService_,
    _CommandService_, _$stateParams_, _$timeout_, _$q_) {

    $scope              = $rootScope.$new();
    $scope.config       = {'APPLICATION_NAME': "Beer Garden"};
    $stateParams        = _$stateParams_;
    $timeout            = _$timeout_;
    $stateParams.id     = 'systemId';
    MockCommandService  = sinon.stub(_CommandService_);
    MockSystemService   = sinon.stub(_SystemService_);
    MockSystemService.getSystem.returns(_$q_.defer().promise);

    $controller('SystemViewController', { $scope: $scope,
      SystemService: MockSystemService, CommandService: MockCommandService });
  }));

  describe("init", function() {

    it("should call getSystem on load", function() {
      sinon.assert.calledOnce(MockSystemService.getSystem)
      sinon.assert.calledWith(MockSystemService.getSystem, 'systemId');
    });

  }); // End Describe init

}); // End Describe CommandIndexController
