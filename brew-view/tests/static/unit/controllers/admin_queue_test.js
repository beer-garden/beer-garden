describe("QueueIndexController", function() {

  var sandbox, deferredGet, $stateParams, $interval, $state, $q, $scope,
      MockQueueService;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));
  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function($rootScope, $controller, _$window_, _$interval_, _QueueService_, _$q_) {
    $scope           = $rootScope.$new();
    $window          = _$window_;
    $interval        = _$interval_;
    $q               = _$q_;

    deferredGet      = $q.defer();
    MockQueueService = sandbox.stub(_QueueService_);
    MockQueueService.getQueues.returns(deferredGet.promise);

    $scope.config = {AMQ_HOST: 'server', AMQ_PORT: 5672, AMQ_ADMIN_PORT: 15672};

    $controller('QueueIndexController', {$scope: $scope, $window: $window, $interval: $interval,
                                         QueueService: MockQueueService});
  }));

  describe("init", function() {

    it("should call getQueues", function() {
      sinon.assert.calledOnce(MockQueueService.getQueues);
    });

  });

  describe("$destroy", function() {

    it("should cancel the $interval", function() {
      $interval.cancel = sinon.spy();
      $scope.$broadcast("$destroy");
      sinon.assert.calledOnce($interval.cancel);
    });

  }); // End Describe $destroy

  describe("clearQueue", function() {

    it("should call clearQueue", function() {
      var deferred = $q.defer();
      deferred.resolve("Hooray!");
      var promise  = deferred.promise;

      promise.success = function(fn) {
        promise.then(function(response) {
          console.log("success");
        });
        return promise;
      };

      promise.error = function(fn) {
        promise.then(function(response) {
          console.log("error");
        });
        return promise;
      };

      MockQueueService.clearQueue.returns(promise)
      $scope.clearQueue('name');
      sinon.assert.calledOnce(MockQueueService.clearQueue)
      sinon.assert.calledWith(MockQueueService.clearQueue, 'name')
    });

  }); // End describe clearQueue

  describe("clearAllQueues", function() {

    it("should call clearQueues", function() {
      var deferred = $q.defer();
      deferred.resolve("Hooray!");
      var promise  = deferred.promise;

      promise.success = function(fn) {
        promise.then(function(response) {
          console.log("success");
        });
        return promise;
      };

      promise.error = function(fn) {
        promise.then(function(response) {
          console.log("error");
        });
        return promise;
      };

      MockQueueService.clearQueues.returns(promise);

      $scope.clearAllQueues();
      sinon.assert.calledOnce(MockQueueService.clearQueues)
    });

  }); // End describe clearAllQueues

  describe("closeAlert", function() {

    it("should remove the element from the alerts array based on index", function() {
      $scope.alerts = [1];
      $scope.closeAlert(0);
      expect($scope.alerts.length).to.equal(0);
    });

  }); // End describe closeAlert

  describe("addSuccessAlert", function() {

    it('should add an alert to the array', function() {
      $scope.addSuccessAlert({message:'my_message'});
      expect($scope.alerts.length).to.equal(1);
      var myAlert = $scope.alerts[0];
      expect(myAlert.type).to.equal('success');
      expect(myAlert).to.have.property('msg');
    });

  }); // End describe addSuccessAlert

  describe("addErrorAlert", function() {

    it('should add an alert to the array', function() {
      $scope.addErrorAlert({message:'my_message'});
      expect($scope.alerts.length).to.equal(1);
      var myAlert = $scope.alerts[0];
      expect(myAlert.type).to.equal('danger');
      expect(myAlert).to.have.property('msg');
    });

  }); // End describe addErrorAlert

}); // End Describe RequestViewController
