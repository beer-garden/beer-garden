Beer Garden
=================================

[![PyPi Version](https://img.shields.io/pypi/v/beer-garden.svg)](https://pypi.python.org/pypi/beer-garden/)
[![Integration Tests](https://github.com/beer-garden/beer-garden/actions/workflows/integration_tests.yml/badge.svg)](https://github.com/beer-garden/beer-garden/actions/workflows/integration_tests.yml)
[![CodeCov](https://codecov.io/gh/beer-garden/beer-garden/branch/develop/graph/badge.svg)](https://codecov.io/gh/beer-garden/beer-garden)

Looking for better documentation? Check out the dedicated documentation at [beer-garden.io](https://beer-garden.io)!

Beer Garden is a framework that provides a standardized interface for Command and Control of systems through the use of plugins.

Take a look at the demo:

![Beer Garden Demo](https://github.com/beer-garden/beer-garden.io/raw/master/images/demo.gif)

## Getting Started

These instructions assume you want a developer installation of Beer-garden. If you want to do work on the Beer-garden framework, this is for you! On the other hand, if you're more interested in trying out Beer-garden or working on a plugin then you may have more luck with the documentation at [beer-garden.io](https://beer-garden.io).

### Pre-requisites:

Beer-garden is a Python application. As of Beer-garden version 3 the minimum required Python version is 3.7.

Beer-garden requires running RabbitMQ and MongoDB servers. If you need help installing these the [docs](https://beer-garden.io) are the place to go!

### Get Up and Running

First, clone this repo:

```
git clone git@github.com:beer-garden/beer-garden.git
```

#### Start the REST API

The Beer-garden application is located in `src/app`. Navigate to that directory and install the python dependencies:

```
pip install -r requirements.txt
```

There's a helper script for running the application in the `bin` directory, and example configs in the `example_config` directory. So an easy way to start the application is like this:

```
python bin/app.py -c example_configs/config.yaml
```

#### Start the UI

The Beer-garden frontend is located in `src/ui`. Navigate to that directory and install the npm dependencies:

```
npm install
```

Then you'll be able to run the development web server. This will listen on port 8080 and forward requests to the Beer-garden API to port 2337:

```
npm run serve
```

## All Done

That's it! You should be able to work on Beer-garden now!
