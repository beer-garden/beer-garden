'use strict';

describe('Brew View', function() {

  it('should automatically redirect to / when location hash/fragment is unknown or empty', function() {
    browser.get('#/foobar');
    expect(browser.getLocationAbsUrl()).toMatch("/");
  });

});
