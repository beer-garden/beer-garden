describe("CommandService", function() {

  var service, sandbox, $scope, $rootScope, $httpBackend;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));

  beforeEach(inject(function(_CommandService_, _$rootScope_, _$httpBackend_) {
    service      = _CommandService_;
    $rootScope   = _$rootScope_;
    $scope       = _$rootScope_.$new();
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

  describe("systems", function() {

    var fakeSystem, command;

    beforeEach(function() {
      fakeSystem = {id: '123', name: 'test-system'};
      command = { system: {id: 123} };
      $rootScope.systems = [fakeSystem];
    });

    it("findSystem should correctly return a system", function() {
      expect(service.findSystem(command)).to.equal(fakeSystem);
    });

    it("getSystemName should correctly determine the system name", function() {
      expect(service.getSystemName(command)).to.equal(fakeSystem.name);
    });

  }); // End Describe systems

  describe("getCommands", function() {

    var commands = [{name:'command1'}, {name:'command2'}];

    beforeEach(function() {
      $httpBackend.whenGET('api/v1/commands').respond(commands);
      sinon.stub(service, 'getSystemName', function() {return 'system';});
    });

    it("should call to the backend", function() {
      $httpBackend.expectGET('api/v1/commands');
      service.getCommands();
      $httpBackend.flush();
    });

  }); // End Describe getCommands

  describe("getCommand", function() {

    it("should call to the backend", function() {
      $httpBackend.expectGET('api/v1/commands/id').respond('command1');
      service.getCommand('id');
      $httpBackend.flush();
    });

  }); // End Describe getCommand

}); // End Describe CommandService
