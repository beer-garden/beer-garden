
==============
User Interface
==============

This is the Beer-garden application frontend. It's an AngularJS (1.x) application.

|gitter| |travis| |codecov|

.. |gitter| image:: https://img.shields.io/badge/gitter-Join%20Us!-ff69b4.svg
   :target: https://gitter.im/beer-garden-io/Lobby
   :alt: Gitter

.. |travis| image:: https://img.shields.io/travis/beer-garden/beer-garden.svg
   :target: https://travis-ci.org/beer-garden/beer-garden?branch=v3
   :alt: Build Status

.. |codecov| image:: https://codecov.io/gh/beer-garden/garden/branch/v3/graph/badge.svg
   :target: https://codecov.io/gh/beer-garden/beer-garden
   :alt: Code Coverage


Getting Started
===============

The following steps are the easiest way to get up and running.

Prerequisites
-------------

* Node.js (Stable, 6+)
* The Beer-garden application running with an HTTP entry-point

Get Up and Running
------------------

Start the development server:

.. code-block:: console

    $ npm run serve

Sweet! Everything should now be up and running. Visit http://localhost:8080/ in a browser to check it out. Hit Ctrl-c to stop the web server.

NOTE: It's worth noting that the JavaScript App is served on 8080 but it expects the Beer-garden REST API to be availible on port 2337.


Configuration
=============

To change the server configuration you'll need to modify webpack.dev.js. You'll need to restart the web server after making any changes.


Testing and Code Coverage
=========================

You can run the testing yourself.

JavaScript
----------

We are currently lacking in good JavaScript tests since we switched to webpack. We are hoping to remedy this in the near-term future. You __should__ be able to run tests:

.. code-block:: console

    $ make test

To run ESLint:

.. code-block:: console

    make lint

Distribution
============

Creating the distribution is simple. Simply run the following:

.. code-block:: console

    $ make package


