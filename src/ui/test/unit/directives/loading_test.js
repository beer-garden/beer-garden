'use strict';

describe('Loading Directive', function() {
  var scope, $compile, element;

  beforeEach(module('templates'));
  beforeEach(module('bgApp'));
  beforeEach(inject(function(_$compile_, $rootScope) {
    $compile        = _$compile_;
    scope          = $rootScope.$new();
  }));

  var create = function() {
    var elem, compiledElem;
    elem = angular.element('<div><loading loader="myLoader" delay="0"></loading></div>');
    compiledElem = $compile(elem)(scope);
    scope.$digest();
    return compiledElem;
  }

  it("should generate nothing if loaded is true", function() {
    scope.myLoader = {loaded: true, error: false, data: [], status: null};
    var element = create();
    scope.$apply();

    expect(element.text()).to.equal('');
  });

  it("should generate nothing if error is true", function() {
    scope.myLoader = {loaded: false, error: true, data: [], status: null};
    var element = create();
    scope.$apply();

    expect(element.text()).to.equal('');
  });

  it("should generate a large spinner", function() {
    scope.myLoader = {loaded: false, error: false, data: [], status: 200};
    var element = create();
    scope.$apply();

    var mainDiv = angular.element(element.contents()[1]);
    var h2      = angular.element(mainDiv.contents()[0]);
    expect(h2).to.exist;

    var i       = angular.element(h2.contents()[0]);
    expect(i).to.exist;
    expect(i.hasClass('fa')).to.equal(true);
    expect(i.hasClass('fa-cog')).to.equal(true);
    expect(i.hasClass('fa-spin')).to.equal(true);
    expect(i.hasClass('fa-2x')).to.equal(true);
  });

});
