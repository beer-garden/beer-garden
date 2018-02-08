describe("RequestIndexController", function() {

  var sandbox,
      $scope,
      registerStub;

  beforeEach(module('bgApp'));

  beforeEach(inject(function($rootScope, $controller, _DTOptionsBuilder_, _DTColumnBuilder_, _DTRendererService_) {
    sandbox = sinon.sandbox.create();
    $scope  = $rootScope.$new();
    registerStub = sinon.stub(_DTRendererService_, "registerPlugin");
    $controller('RequestIndexController', {$scope: $scope, DTRendererService: _DTRendererService_});
  }));

  afterEach(function() {
    sandbox.restore();
  });

  describe("dtOptions", function() {

    it("should set things up correctly", function() {
      expect($scope.dtOptions.hasBootstrap).to.equal(true);
      expect($scope.dtOptions.sPaginationType).to.equal('full_numbers');
      expect($scope.dtOptions.hasLightColumnFilter).to.equal(true);
    });

    it("should have the right value for IN_PROGRESS", function() {
      values = $scope.dtOptions.lightColumnFilterOptions[2].values;
      for(var i=0; i < values.length; i++) {
        if(values[i].label == 'IN PROGRESS') {
          expect(values[i].value).to.equal('IN_PROGRESS');
        }
      }
    });

  }); // End Describe dtOptions

  describe("dtColumns", function() {

    it("should create the command column", function() {
      expect($scope.dtColumns[0].mData).to.equal('command');
      expect($scope.dtColumns[0].sTitle).to.equal('Command Name');
      expect($scope.dtColumns[0]).to.have.property('mRender');
    });

    it("should correctly create the system column", function() {
      expect($scope.dtColumns[1].mData).to.equal("system");
      expect($scope.dtColumns[1].sTitle).to.equal("System");
      expect($scope.dtColumns[1]).to.have.property('mRender');
    });

    it("should create the status column", function() {
      expect($scope.dtColumns[2].mData).to.equal('status');
      expect($scope.dtColumns[2].sTitle).to.equal('Status');
    });

    it('should create the created_at column', function() {
      expect($scope.dtColumns[3].mData).to.equal('created_at');
      expect($scope.dtColumns[3].sTitle).to.equal('Created');
      expect($scope.dtColumns[3].type).to.equal('date');
      expect($scope.dtColumns[3]).to.have.property('mRender');
    });

    it("should create the comment column", function() {
      expect($scope.dtColumns[4].mData).to.equal('comment');
      expect($scope.dtColumns[4].sTitle).to.equal('Comment');
    });

  });// End Describe dtColumns

  describe("dtRendererService", function() {

    it("should specify a postRender function", function() {
      expect(registerStub).to.have.been.called;
    });

    it("should correctly render the columns", function() {
      expect($scope.dtColumns[0].mRender('command', 'type', {id:'requestId'}))
        .to.equal('<a href="#!/requests/requestId">command</a>');

      expect($scope.dtColumns[1].mRender('system', 'type', {})).to.equal('system');
      expect($scope.dtColumns[1].mRender('system', 'type', {instance_name: 'foo'})).to.equal('system [foo]');
      expect($scope.dtColumns[1].mRender('system', 'type', {metadata: {system_display_name: 'Display'}})).to.equal('Display');

      expect($scope.dtColumns[3].mRender('Mon, 24 Aug 2015 20:23:14 -0000', 'type', {}))
        .to.deep.equal(new Date('Mon, 24 Aug 2015 20:23:14 -0000'));
    });

  });

}); // End Describe CommandIndexController
