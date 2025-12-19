

Beer-Garden App
===========================

This is the Beer-garden application backend.

[![PyPi Version](https://img.shields.io/pypi/v/beer-garden.svg)](https://pypi.python.org/pypi/beer-garden/)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
[![CodeCov](https://codecov.io/gh/beer-garden/beer-garden/branch/develop/graph/badge.svg)](https://codecov.io/gh/beer-garden/beer-garden)


Getting Started
===============

Pre-requisites
--------------

* Python >= 3.11
* pip
* Connectivity to MongoDB Server  - (Tested on 6.0, Optimized for 7.0+)
* Connectivity to Rabbitmq-Server - (Tested on 3.8)


Get Up and Running
------------------

When installed from pip you can simply:

```
$ beer-garden -c /path/to/config.json
```
These are the minimum required steps once you have all the pre-requisites up and running.

```
$ git clone https://github.com/beer-garden/beer-garden.git
$ cd src/app
$ pip install -r requirements.txt
$ ./bin/app.sh
```

There are several plugins that are loaded by default. You can view them in the UI.


Testing
=======

Running the tests:

```
$ make test
```

Generating coverage:

```
$ make coverage
```

Linting:
```
$ make lint
```
Credits
=======

* Doug Hellmann (@doughellmann) - Doug originally owned the bartender name but was willing to allow us to have it so that we didn't have to change a lot of documentation back when the application needed the name. Thanks very much Doug!
