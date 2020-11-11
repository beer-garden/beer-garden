'use strict';

describe('Server Error Directive', function() {
  var scope, $compile, element;

  beforeEach(module('templates'));
  beforeEach(module('bgApp'));
  beforeEach(inject(function(_$compile_, $rootScope) {
    $compile        = _$compile_;
    scope          = $rootScope.$new();
  }));

  var create = function() {
    var elem, compiledElem;
    elem = angular.element('<div><server-error loader="myLoader"></server-error></div>');
    compiledElem = $compile(elem)(scope);
    scope.$digest();
    return compiledElem;
  }

  it("should generate nothing if error is false", function() {
    scope.myLoader = {loaded: false, error: false, data: [], status: 500};
    var element = create();
    scope.$apply();

    expect(element.text()).to.equal('');
  });

  it("should generate nothing if error is true but the status is 404", function() {
    scope.myLoader = {loaded: false, error: true, data: [], status: 404};
    var element = create();
    scope.$apply();

    expect(element.text()).to.equal('');
  });

  it('should add the correct attributes onto the mainDiv', function() {
    scope.myLoader = {loaded: false, error: true, data: [], status: 500};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    expect(mainDiv.hasClass('col-md-12')).to.equal(true);
  });

  it("should generate a panel child onto the mainDiv", function() {
    scope.myLoader = {loaded: false, error: true, data: [], status: 500};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    expect(mainDiv.contents().length).to.equal(1);
  });

  it('should generate a panel with the correct class', function() {
    scope.myLoader = {loaded: false, error: true, data: [], status: 500};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    expect(panel).to.exist;
    expect(panel.hasClass('panel')).to.equal(true);
    expect(panel.hasClass('panel-danger')).to.equal(true);
  });

  it("should generate a panel with 3 children", function() {
    scope.myLoader = {loaded: false, error: true, data: [], status: 500};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    expect(panel.contents().length).to.equal(3);
  });

  it('should generate a valid panel heading', function() {
    scope.myLoader = {loaded: false, error: true, data: [], status: 500};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelHeading = angular.element(panel.contents()[0]);

    expect(panelHeading).to.exist;
    expect(panelHeading.hasClass('panel-heading')).to.equal(true);
  });

  it('should generate a valid panelBody', function() {
    scope.myLoader = {loaded: false, error: true, data: [], status: 500};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelBody = angular.element(panel.contents()[1]);

    expect(panelBody).to.exist;
    expect(panelBody.hasClass('panel-body')).to.equal(true);
  });

  it("should use the server error message", function() {
    scope.myLoader = {loaded: false, error: true, data: [], status: 500, errorMessage: 'myErrorMessage'};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelBody = angular.element(panel.contents()[1]);
    var dl        = angular.element(panelBody.contents()[0]);
    var dd        = angular.element(dl.find('dd')[0]);

    expect(dd.text()).to.equal('myErrorMessage');
  });

  it('should generate a valid panel footer', function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelFooter = angular.element(panel.contents()[2]);

    expect(panelFooter).to.exist;
  });

});
