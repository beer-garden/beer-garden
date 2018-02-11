describe("CommandIndexController", function() {

  var sandbox, $scope, MockSystemService, MockCommandService;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));
  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function($rootScope, $controller, _$q_, _SystemService_, _CommandService_) {
    $scope              = $rootScope.$new();
    MockSystemService   = sinon.stub(_SystemService_);
    MockCommandService  = sinon.stub(_CommandService_);
    MockCommandService.getCommands.returns(_$q_.defer().promise);

    $controller('CommandIndexController', {$scope: $scope, SystemService: MockSystemService,
                                           CommandService: MockCommandService});
  }));

  describe("getData", function() {

    it("should have called getCommands", function() {
      sinon.assert.calledOnce(MockCommandService.getCommands);
    });

  }); // End Describe getData

}); // End Describe CommandIndexController
