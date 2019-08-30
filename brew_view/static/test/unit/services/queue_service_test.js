describe("QueueService", function() {

  var service, sandbox, $httpBackend;


  beforeEach(module('bgApp'));
  beforeEach(module('templates'));
  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function(_QueueService_, _$httpBackend_) {
    service     = _QueueService_
    $httpBackend = _$httpBackend_;
  }));

  afterEach(function() {
    $httpBackend.verifyNoOutstandingExpectation();
    $httpBackend.verifyNoOutstandingRequest();
  });

  describe("getQueues", function() {

    it("should call to the backend", function() {
      $httpBackend.expectGET('api/v1/admin/queues').respond(['queue1', 'queue2']);
      service.getQueues();
      $httpBackend.flush();
    });

  }); // End Describe getQueues

  describe("clearQueues", function() {

    it("should call delete correctly", function() {
      $httpBackend.expectDELETE("api/v1/admin/queues").respond(200, {});
      service.clearQueues();
      $httpBackend.flush();
    });

  }); // End Describe clearQueues

  describe("clearQueue", function() {

    it("should call delete correctly", function() {
      $httpBackend.expectDELETE("api/v1/admin/queues/name").respond(200, {});
      service.clearQueue('name');
      $httpBackend.flush();
    });

  }); // End Describe clearQueue

}); // End Describe QueueService
