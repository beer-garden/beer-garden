describe("SystemService", function() {

  var service, sandbox, $httpBackend;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));

  beforeEach(inject(function(_SystemService_, _$httpBackend_) {
    service     = _SystemService_
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

  describe("getSystems", function() {

    it("should call to the backend", function() {
      $httpBackend.expectGET('api/v1/systems').respond(['system1', 'system2']);
      service.getSystems();
      $httpBackend.flush();
    });

  }); // End Describe getSystems

  describe("getSystem", function() {

    it("should call to the backend", function() {
      $httpBackend.expectGET('api/v1/systems/id').respond('system1');
      service.getSystem('id');
      $httpBackend.flush();
    });

  }); // End Describe getSystem

}); // End Describe SystemService
