describe("VersionService", function() {

  var service, sandbox, $httpBackend;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));

  beforeEach(inject(function(_VersionService_, _$httpBackend_) {
    service     = _VersionService_
    $httpBackend = _$httpBackend_;
  }));

  beforeEach(function() {
    sandbox = sinon.sandbox.create();
  });

  afterEach(function() {
    sandbox.restore();
    $httpBackend.verifyNoOutstandingExpectation();
    $httpBackend.verifyNoOutstandingRequest();
  });

  describe("getVersionInfo", function() {

    it("should call to the backend", function() {
      $httpBackend.expectGET('version').respond(['version1', 'version2']);
      service.getVersionInfo();
      $httpBackend.flush();
    });

  }); // End Describe getVersionInfo

}); // End Describe VersionService
