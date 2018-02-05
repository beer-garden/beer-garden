describe("RequestService", function() {

  var service, sandbox, $httpBackend;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));

  beforeEach(function() {
    sandbox = sinon.sandbox.create();
  });
  afterEach(function() {
    sandbox.restore();
    $httpBackend.verifyNoOutstandingExpectation();
    $httpBackend.verifyNoOutstandingRequest();
  });

  beforeEach(inject(function(_RequestService_, _$httpBackend_) {
    service     = _RequestService_
    $httpBackend = _$httpBackend_;
  }));

  describe("Request API functions", function() {

    it("getRequests should call to the backend", function() {
      $httpBackend.expectGET('api/v1/requests').respond(['request1', 'request2']);
      service.getRequests();
      $httpBackend.flush();
    });

    it("getRequest should call to the backend", function() {
      $httpBackend.expectGET('api/v1/requests/id').respond('request1');
      service.getRequest('id');
      $httpBackend.flush();
    });

    it("createRequest should call to the backend", function() {
      $httpBackend.expectPOST('api/v1/requests', {}).respond({});
      service.createRequest({});
      $httpBackend.flush();
    });

  }); // End Request API functions

  describe("getCommandId", function() {

    it("should call to the backend", function() {
      var request = { system: 'systemName' }
      $httpBackend.expectGET('api/v1/systems?include_commands=true&name=systemName').respond(200, [])
      service.getCommandId(request);
      $httpBackend.flush();
    });

    it("should return a null to a then if there is no data returned", function() {
      var request = {system: 'systemName', command: 'commandName'}
      $httpBackend.expectGET('api/v1/systems?include_commands=true&name=systemName').respond(200, [])
      service.getCommandId(request).then(function(data) {
        expect(data).to.equal(null);
      });
      $httpBackend.flush();
    });

    it('should return a null to a then if the command no longer exists', function() {
      var request = {system: 'systemName', command: 'commandName'}
      $httpBackend.expectGET('api/v1/systems?include_commands=true&name=systemName').respond(200, [{commands: [{name:'foo'}]}])
      service.getCommandId(request).then(function(data) {
        expect(data).to.equal(null);
      });
      $httpBackend.flush();
    });

    it('should return the id if the command exists', function() {
      var request = {system: 'systemName', command: 'commandName'}
      $httpBackend.expectGET('api/v1/systems?include_commands=true&name=systemName').respond(200, [{commands: [{name:'commandName', id: 'id'}]}])
      service.getCommandId(request).then(function(data) {
        expect(data).to.equal('id');
      });
      $httpBackend.flush();
    });

  }); // End describe getCommandId

});
