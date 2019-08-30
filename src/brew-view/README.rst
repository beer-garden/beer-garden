
=========
Brew View
=========

Brew View is the beer-garden application frontend. It uses Tornado to serve some REST endpoints and the AngularJS application, and it communicates with the beer-garden backend (Bartender) through Thrift.

|gitter| |pypi| |travis| |codecov| |docs| |pyup|

.. |gitter| image:: https://img.shields.io/badge/gitter-Join%20Us!-ff69b4.svg
   :target: https://gitter.im/beer-garden-io/Lobby
   :alt: Gitter

.. |pypi| image:: https://img.shields.io/pypi/v/brew-view.svg
   :target: https://pypi.python.org/pypi/brew-view
   :alt: PyPI

.. |travis| image:: https://img.shields.io/travis/beer-garden/brew-view.svg
   :target: https://travis-ci.org/beer-garden/brew-view?branch=master
   :alt: Build Status

.. |codecov| image:: https://codecov.io/gh/beer-garden/brew-view/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/beer-garden/brew-view
   :alt: Code Coverage

.. |docs| image:: https://readthedocs.org/projects/brew-view/badge/?version=latest
   :target: https://brew-view.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. |pyup| image:: https://pyup.io/repos/github/beer-garden/brew-view/shield.svg
   :target: https://pyup.io/repos/github/beer-garden/brew-view/
   :alt: Pyup Updates

Getting Started
===============

The following steps are the easiest way to get Brew-view up and running from source.

Prerequisites
-------------

* Python (2.7.9+ or 3.4+)
* Node.js (Stable, 6+) with `yarn` installed globally
* Connectivity to a MongoDB Server
* Connectivity to a RabbitMQ Server

Get Up and Running
------------------

A full installation guide for RabbitMQ and Mongo is outside the scope of this document. Below is a small snippet to get you up and running if you have ``docker`` installed..

.. code-block:: console

    $ docker run -d -p 27017:27017 --name bg-mongo mongo
    $ docker run -d -p 5672:5672 -p 15672:15672 --name bg-rmq rabbitmq:3-management-alpine


To do development locally, it is important to note that brew-view is a combination of a python API powered by ``tornado`` and an AngularJS App. So we will start them both up!

.. code-block:: console

    $ git clone https://github.com/beer-garden/brew-view.git
    $ cd brew-view
    $ make deps # just a simple way to do pip install -r requirements.txt and yarn install

Start up the JavaScript Application:

.. code-block:: console

    $ cd brew_view/static
    $ yarn serve

Now start up the Python API:

.. code-block:: console

    $ cd /path/to/brew-view
    $ python -m brew_view -c ./dev_conf/config.yml

Sweet! Everything should now be up and running. Visit http://localhost:8080/ in a browser to check it out. Hit Ctrl-c to stop the web server.

NOTE: It's worth noting that the JavaScript App is served on 8080 but the python application is running on 2337.


Configuration
=============

There's a conf/config.yml file that comes with the installation. It comes with sensible default values but feel free to change them if you'd like. You'll need to restart the web server after making any changes.


REST Services
================

Brew-view's most visible job is to serve the frontend application, but it also provides a REST API. This API is used by the frontend (and the plugins) to interact with the rest of beer-garden. You're more than welcome to use the REST API directly if you'd like - you can find Swagger documentation by navigating to the `About` page and clicking the `Check it out!` button.

Testing and Code Coverage
=========================

You can run the testing yourself.

Python
------

.. code-block:: console

    $ make test

This will run the tests for the python application. You can run against multiple python versions using tox:

.. code-block:: console

    $ make test-all

To generate coverage:

.. code-block:: console

    $ make coverage

We use ``flake8`` for linting:

.. code-block:: console

    $ make lint

JavaScript
----------

The JavaScript application has its own ``Makefile`` so to run these commands you'll need to be in the ``brew_view/static`` directory.

We are currently lacking in good JavaScript tests since we switched to webpack. We are hoping to remedy this in the near-term future. You __should__ be able to run tests:

.. code-block:: console

    $ make test

To run ESLint:

.. code-block:: console

    make lint

Distribution
============

Creating the brew-view distribution is simple. Simply go to the git root directory and run the following:

.. code-block:: console

    $ make dist


