Brew View
=================================

Brew View is the beer-garden application frontend. It uses Tornado to serve some REST endpoints and the AngularJS application, and it communicates with the beer-garden backend (Bartender) through Thrift.


## Getting Started

The following steps are the easiest way to get Brew-view up and running from source.

### Prerequisites:

* Python (2.7.9+ or 3.4+)
* Node.js (Stable, 6+) with `yarn` installed globally
* Connectivity to a MongoDB Server

### Get Up and Running

```bash
# Clone the repository
git clone https://github.com/beer-garden.git
cd beer-garden/brew-view

# Install node dependencies and build frontend
pushd brew_view/static
yarn install && yarn build
popd

# Install Python dependencies
pip install -r requirements.txt

# Run the application
bin/app.sh
```

Sweet! Everything should now be up and running. Visit http://localhost:2337/ in a browser to check it out. Hit Ctrl-c to stop the web server.


## Configuration

There's a conf/config.json file that comes with the installation. It comes with sensible default values but feel free to change them if you'd like. You'll need to restart the web server after making any changes.


## REST Services

Brew-view's most visible job is to serve the frontend application, but it also provides a REST API. This API is used by the frontend (and the plugins) to interact with the rest of beer-garden. You're more than welcome to use the REST API directly if you'd like - you can find Swagger documentation by navigating to the `About` page and clicking the `Check it out!` button.

## Testing and Code Coverage

### Python

```bash
# In the 'brew-view' directory
# To run the tests:
nosetests

# To generate code coverage:
bin/generate_coverage.sh
```

Running the code coverage script will:
* Print results to STDOUT
* Generate Cobertura and xUnit test result reports in the `output/python` directory
* Generate an html report at `output/python/html/index.html`
