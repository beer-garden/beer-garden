describe("SystemAdminController", function() {

  var sandbox, controller,
      $timeout, $rootScope, $scope, MockSystemService;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));
  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function($rootScope, $controller, _$interval_, _$http_,
      _$httpBackend_, _$q_, _SystemService_, _InstanceService_) {
    $scope            = $rootScope.$new();
    $rootScopeMock    = $rootScope.$new();
    $interval         = _$interval_;
    $http             = _$http_;
    $q                = _$q_;

    deferred          = $q.defer();
    MockSystemService = sandbox.stub(_SystemService_)
    MockSystemService.getSystems.returns(deferred.promise);
    MockInstanceService = sandbox.stub(_InstanceService_);

    controller = $controller('SystemAdminController', {
      $scope: $scope, $rootScope: $rootScopeMock, $interval: $interval,
      $http: $http, SystemService: MockSystemService,
      InstanceService: MockInstanceService});
  }));

  describe("init", function() {

    it("should call getSystems", function() {
      expect(MockSystemService.getSystems).to.have.been.called.once;
    });

  });

  describe("system actions", function() {

    it("should rescan when directed", inject(function($httpBackend) {
      $httpBackend.expectPATCH('api/v1/admin/').respond('');
      $scope.rescan();
      $httpBackend.flush();

      $httpBackend.verifyNoOutstandingExpectation();
      $httpBackend.verifyNoOutstandingRequest();
    }));

    it("should start all instances when directed", function() {
      $scope.startSystem({instances: [1, 2]});
      expect(MockInstanceService.startInstance).to.have.been.called.twice;
    });

    it("should stop all instances when directed", function() {
      $scope.stopSystem({instances: [1, 2]});
      expect(MockInstanceService.stopInstance).to.have.been.called.twice;
    });

    it("should reload when directed", function() {
      $scope.reloadSystem('');
      expect(MockSystemService.reloadSystem).to.have.been.called;
    });

    it("should delete when directed", function() {
      $scope.deleteSystem('');
      expect(MockSystemService.deleteSystem).to.have.been.called;
    });

  }); // End Describe system actions

  describe("hasRunningInstances", function() {

    it("should detect when a system has running instances", function() {
      expect($scope.hasRunningInstances(
        {instances: [{status: 'RUNNING'}, {status: 'STOPPED'}]})).to.be.true;
      expect($scope.hasRunningInstances(
        {instances: [{status: 'STOPPED'}, {status: 'STOPPED'}]})).to.be.false;
    });

  }); // End Describe hasRunningInstances

  describe("instance actions", function() {

    it("should start when directed", function() {
      $scope.startInstance('');
      expect(MockInstanceService.startInstance).to.have.been.called;
    });

    it("should stop when directed", function() {
      $scope.stopInstance('');
      expect(MockInstanceService.stopInstance).to.have.been.called;
    });

  });

  describe("system update", function() {

    it("should update system list every so often", function() {
      expect(MockSystemService.getSystems).to.have.been.called.once;
      $interval.flush(6);
      expect(MockSystemService.getSystems).to.have.been.called.twice;
    });

  }); // End Describe system update

  describe("$destroy", function() {

    it("should kill status_update", function() {
      $interval.cancel = sinon.spy();
      $scope.$broadcast('$destroy');
      expect($interval.cancel).to.have.been.called;
    });

  }); // End Describe $destroy

}); // End Describe SystemAdminController
