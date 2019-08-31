
=========
Bartender
=========

Bartender is the beer-garden backend. It's responsible for maintaining plugin health/status and running the actual plugins.

|gitter| |pypi| |travis| |codecov| |docs| |pyup|

.. |gitter| image:: https://img.shields.io/badge/gitter-Join%20Us!-ff69b4.svg
   :target: https://gitter.im/beer-garden-io/Lobby
   :alt: Gitter

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

When installed from pip you can simply:

.. code-block:: console

    $ bartender -c /path/to/config.json

These are the minimum required steps once you have all the pre-requisites up and running.

.. code-block:: console

    $ git clone https://github.com/beer-garden/bartender.git
    $ cd bartender
    $ pip install -r requirements.txt
    $ ./bin/app.sh # Requires brew-view to be running


There are several plugins that are loaded by default. You can view them in the brew-view UI.


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
