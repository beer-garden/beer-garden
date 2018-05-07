# Integration Testing

These tests are meant to ensure that the different parts of Beer-garden work correctly together.

## On Travis
These tests are designed to be run on Travis. The setup will install the requirements.txt and then run `brew-view` and `bartender` in the background. Once the plugins come up Travis will run `pytest rest` to run all the tests.

## Running Locally

If you're running Beer-garden locally you can also run these tests yourself. Just modify `rest/config.json` to tell the tests where to find your Beer-garden and make sure you have `pytest` installed. Run `pytest rest` to kick things off.

## Parts
- Lifecycle: These test that bartender and brew-view can correctly start up and shut down
- Rest: These test the brew-view rest interface
