
=========
Bartender
=========

Bartender is the beer-garden backend. It's responsible for maintaining plugin health/status and running the actual plugins.

|travis| |codecov| |docs| |pyup|

.. |pypi| image:: https://img.shields.io/pypi/v/bartender.svg
   :target: https://pypi.python.org/pypi/bartender
   :alt: PyPI

.. |travis| image:: https://img.shields.io/travis/beer-garden/bartender.svg
   :target: https://travis-ci.org/beer-garden/bartender?branch=master
   :alt: Build Status

.. |codecov| image:: https://codecov.io/gh/beer-garden/bartender/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/beer-garden/bartender
   :alt: Code Coverage

.. |docs| image:: https://readthedocs.org/projects/bartender/badge/?version=latest
   :target: https://bartender.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. |pyup| image:: https://pyup.io/repos/github/beer-garden/bartender/shield.svg
   :target: https://pyup.io/repos/github/beer-garden/bartender/
   :alt: Pyup Updates

Getting Started
===============

Pre-requisites
--------------

* Python >= 2.7, 3.4
* pip
* Connectivity to MongoDB Server  - (Tested on 3.4)
* Connectivity to Rabbitmq-Server - (Tested on 3.6)


Get Up and Running
------------------

These are the minimum required steps once you have all the pre-requisites up and running.

* `git clone https://github.com/beer-garden/bartender.git`
* `cd bartender`
* `pip install -r requirements.txt`
* Ensure that Brew View is running
* `./bin/app.sh`
* Visit: http://localhost:2337/api/v1/systems

There are several plugins that are loaded by default.


Testing
=======

* `cd bartender`
* `nosetests`

Code Coverage
================

* `cd beer-garden`
* `./bin/generate_coverage.sh`
* `Open Firefox`
* Navigate to: `file:///path/to/beer-garden/bartender/output/python/html/index.html`
