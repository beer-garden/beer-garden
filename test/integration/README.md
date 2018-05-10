# Integration Testing

These tests are meant to ensure that the different parts of Beer-garden work correctly together.

## On Travis
These tests are designed to be run on Travis. The setup will install the requirements.txt and then run `brew-view` and `bartender` in the background. Once the plugins come up Travis will run `pytest rest` to run all the tests.

## Running Locally

If you're running Beer-garden locally you can also run these tests yourself. Just modify `rest/config.json` to tell the tests where to find your Beer-garden and make sure you have `pytest` installed. Run `pytest rest` to kick things off.

## Parts
These tests are targeting different aspects of beergarden.

### Lifecycle
These test that bartender and brew-view can correctly start up and shut down

### Rest
These test the brew-view rest interface

### Config
These make sure that configuration file generation / upgrades work properly

Version directories:
These have config files that were used for that version.

Expected:
This are the expected results of updating FROM the specified versions.
For example, running migrate_config_file on 2.0.0/bartender.json should
result in a config that matches expected/2.0.0-bartender.json

### Upgrade
TODO
These test upgrading beer-garden from one version to another
