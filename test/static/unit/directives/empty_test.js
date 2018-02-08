'use strict';

describe('Empty Directive', function() {
  var scope, $compile, element;

  beforeEach(module('templates'));
  beforeEach(module('bgApp'));
  beforeEach(inject(function(_$compile_, $rootScope) {
    $compile        = _$compile_;
    scope          = $rootScope.$new();
  }));

  var create = function() {
    var elem, compiledElem;
    elem = angular.element('<div><empty loader="myLoader" label="myLabel"></empty></div>');
    compiledElem = $compile(elem)(scope);
    scope.$digest();
    return compiledElem;
  }

  it("should generate nothing if loaded is false and the status is not 404", function() {
    scope.myLoader = {loaded: false, error: false, data: [], status: 200};
    var element = create();
    scope.$apply();

    expect(element.text()).to.equal('');
  });

  it("should generate nothing if error is true and the status is not 404", function() {
    scope.myLoader = {loaded: true, error: true, data: [], status: 200};
    var element = create();
    scope.$apply();

    expect(element.text()).to.equal('');
  });

  it("should generate nothing if data is not 0 and the status is not 404", function() {
    scope.myLoader = {loaded: true, error: false, data: [1,2,3], status: 200};
    var element = create();
    scope.$apply();

    expect(element.text()).to.equal('');
  });

  it('should add the correct attributes onto the mainDiv', function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    expect(mainDiv.hasClass('col-md-12')).to.equal(true);
  });

  it("should generate a panel child onto the mainDiv", function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    expect(mainDiv.contents().length).to.equal(1);
  });

  it('should generate a panel with the correct class', function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    expect(panel).to.exist;
    expect(panel.hasClass('panel')).to.equal(true);
    expect(panel.hasClass('panel-warning')).to.equal(true)
  });

  it("should generate a panel with 3 children", function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    expect(panel.contents().length).to.equal(3);
  });

  it('should generate a valid panel heading', function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelHeading = angular.element(panel.contents()[0]);

    expect(panelHeading).to.exist;
    expect(panelHeading.hasClass('panel-heading')).to.equal(true);
  });

  it('should replace the label correctly', function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelHeading = angular.element(panel.contents()[0]);
    var h2           = angular.element(panelHeading.contents()[0]);

    expect(h2.text()).to.contain('myLabel');
  });

  it('should generate a valid panelBody', function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404, errorMap: {'empty': {'solutions': [{problem: 'problem1', description: 'description1', resolution :'resolution1'}]}}};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelBody = angular.element(panel.contents()[1]);

    expect(panelBody).to.exist;
    expect(panelBody.hasClass('panel-body')).to.equal(true);
  });

  it('should add a label to the panel body with the label replaced', function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404, errorMap: {'empty': {'solutions': [{problem: 'problem1', description: 'description1', resolution :'resolution1'}]}}};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelBody = angular.element(panel.contents()[1]);

    expect(panelBody.find('p')).to.exist;
    expect(panelBody.find('p').text()).to.contain('myLabel');
  });

  it('should add a table element to the panel body', function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404, errorMap: {'empty': {'solutions': [{problem: 'problem1', description: 'description1', resolution :'resolution1'}]}}};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelBody = angular.element(panel.contents()[1]);

    expect(panelBody.find('table')).to.exist;
    expect(panelBody.find('table').hasClass('table')).to.equal(true);
  });

  it("should generate a good table header", function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404, errorMap: {'empty': {'solutions': [{problem: 'problem1', description: 'description1', resolution :'resolution1'}]}}};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelBody = angular.element(panel.contents()[1]);
    var table     = panelBody.find('table');

    expect(table.find('th').length).to.equal(3);
  });

  it('should do something with the rest of the table', function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: 404, errorMap: {'empty': {'solutions': [{problem: 'problem1', description: 'description1', resolution :'resolution1'}]}}};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var panel   = angular.element(mainDiv.contents()[0]);
    var panelBody = angular.element(panel.contents()[1]);
    var table     = panelBody.find('table');

    expect(table.find('td').length).to.equal(3);
    var problem     = angular.element(table.find('td')[0]);
    var description = angular.element(table.find('td')[1]);
    var resolution  = angular.element(table.find('td')[2]);
    expect(problem.attr('ng-bind-html')).to.equal('solution.problem');
    expect(description.attr('ng-bind-html')).to.equal('solution.description');
    expect(resolution.attr('ng-bind-html')).to.equal('solution.resolution');

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
