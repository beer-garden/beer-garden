
===========================
Beer-Garden App
===========================

This is the Beer-garden application backend.

|gitter| |pypi| |travis| |codecov|

.. |gitter| image:: https://img.shields.io/badge/gitter-Join%20Us!-ff69b4.svg
   :target: https://gitter.im/beer-garden-io/Lobby
   :alt: Gitter

.. |pypi| image:: https://img.shields.io/pypi/v/beer-garden.svg
   :target: https://pypi.python.org/pypi/beer-garden
   :alt: PyPI

.. |travis| image:: https://img.shields.io/travis/beer-garden/beer-garden.svg
   :target: https://travis-ci.com/beer-garden/beer-garden
   :alt: Build Status

.. |codecov| image:: https://codecov.io/gh/beer-garden/garden/branch/v3/graph/badge.svg
   :target: https://codecov.io/gh/beer-garden/beer-garden
   :alt: Code Coverage

Getting Started
===============

Pre-requisites
--------------

* Python >= 3.7
* pip
* Connectivity to MongoDB Server  - (Tested on 3.4)
* Connectivity to Rabbitmq-Server - (Tested on 3.6)


Get Up and Running
------------------

When installed from pip you can simply:

.. code-block:: console

    $ beer-garden -c /path/to/config.json

These are the minimum required steps once you have all the pre-requisites up and running.

.. code-block:: console

    $ git clone https://github.com/beer-garden/beer-garden.git
    $ cd src/app
    $ pip install -r requirements.txt
    $ ./bin/app.sh


There are several plugins that are loaded by default. You can view them in the UI.


Testing
=======

Running the tests:

.. code-block:: console

    $ make test

Generating coverage:

.. code-block:: console

    $ make coverage

Linting:

.. code-block:: console

    $ make lint

Credits
=======

* Doug Hellmann (@doughellmann) - Doug originally owned the bartender name but was willing to allow us to have it so that we didn't have to change a lot of documentation. Thanks very much Doug!
