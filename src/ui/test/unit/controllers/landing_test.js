describe("LandingController", function() {

  var sandbox, $scope, $location, MockSystemService;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));
  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function($rootScope, $controller, _$location_, _$q_, _SystemService_) {
    $scope              = $rootScope.$new();
    $location           = _$location_;
    MockSystemService   = sinon.stub(_SystemService_);
    MockSystemService.getSystems.returns(_$q_.defer().promise);

    $controller('LandingController', { $scope: $scope, SystemService: MockSystemService });
  }));

  describe("init", function() {

    it("should call getSystems on load", function() {
      sinon.assert.calledOnce(MockSystemService.getSystems)
    });

  }); // End Describe init

  describe("exploreSystem", function() {

    it("should change the location", function() {
      $scope.exploreSystem('systemId');
      expect($location.path()).to.be.equal('/systems/systemId');
    });

  }); // End Describe exploreSystem

}); // End Describe CommandIndexController
