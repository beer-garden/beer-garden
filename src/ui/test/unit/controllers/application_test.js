describe("ApplicationController", function() {

  var sandbox, $scope, MockUtilityService;

  beforeEach(module('bgApp'));
  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function(_$rootScope_, $controller, _UtilityService_) {
    $scope = _$rootScope_.$new();
    MockUtilityService = sandbox.stub(_UtilityService_);

    $controller('ApplicationController', {$scope: $scope, UtilityService: MockUtilityService});
  }));

  describe("init", function() {

    it("should map scope getIcon to UtilityService", function() {
      $scope.getIcon('fa-beer');
      sinon.assert.calledOnce(MockUtilityService.getIcon);
    });

  });

});
