describe("AboutController", function() {

  var sandbox, deferred, $scope, MockVersionService;

  beforeEach(module('bgApp'));

  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function($rootScope, $controller, _$q_, _VersionService_) {
    $scope = $rootScope.$new();

    deferred = _$q_.defer();
    MockVersionService = sinon.stub(_VersionService_);
    MockVersionService.getVersionInfo.returns(deferred.promise);

    $controller('AboutController', { $scope: $scope, VersionService: MockVersionService });
  }));

  describe("init", function() {

    it("should call getVersionInfo on load", function() {
      sinon.assert.calledOnce(MockVersionService.getVersionInfo);
    });

  }); // End Describe init

  describe("callbacks", function() {

    it("should set everything correctly on success", function() {
      $scope.successCallback({data: 'data'});
      expect($scope.version.data).to.be.equal('data');
      expect($scope.version.loaded).to.be.equal(true);
      expect($scope.version.error).to.be.equal(false);
      expect($scope.version.errorMessage).to.be.equal('');
    });

    it("should set everything correctly on error", function() {
      $scope.failureCallback({data: {message: "foo"}});
      expect($scope.version.data.length).to.be.empty;
      expect($scope.version.loaded).to.be.equal(false);
      expect($scope.version.error).to.be.equal(true);
      expect($scope.version.errorMessage).to.be.equal('foo');
    });

  }); // End describe callbacks

}); // End Describe AboutController
