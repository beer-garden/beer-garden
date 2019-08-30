describe("PromiseTest", function() {

  var sandbox, $scope, $q;

  beforeEach(module('bgApp'));
  beforeEach(module('templates'));

  beforeEach(function() { sandbox = sinon.sandbox.create(); });
  afterEach(function() { sandbox.restore(); });

  beforeEach(inject(function(_$rootScope_, _$q_) {
    $q = _$q_;
    $scope = _$rootScope_.$new();
  }));

  it("should allow for promise resolution", function() {
    var deferred = $q.defer();
    var promise = deferred.promise;
    var resolvedValue;

    promise.then(function(value) {
      resolvedValue = value;
    });

    expect(resolvedValue).to.be.not.defined;

    deferred.resolve('Resolved!');
    expect(resolvedValue).to.be.not.defined;

    $scope.$digest();
    expect(resolvedValue).to.equal('Resolved!');
  });

});
