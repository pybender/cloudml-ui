==================
Manage.py Commands
==================

.. contents:: 
   :depth: 3

To run the manage.py command type:

.. code-block:: console

  python manage.py cmd

in the root directory of the project.

Make sure, that virtual enviroupment was activated.

.. note::

  As background implementation of command line utilities `Flask-Script package <http://flask-script.readthedocs.org/>`_ is used.

Commands defined in Flask-Script
================================

Runserver
---------

Usage:

.. code-block:: console

  python manage.py runserver [-?] [-h HOST] [-p PORT]
                             [--threaded]
                             [--processes PROCESSES] [--passthrough-errors] [-d]
                             [-D] [-r] [-R]

Starts a lightweight development Web server on the local machine. By default, the server runs on port 8000 on the IP address 127.0.0.1. You can pass in an IP address and port number explicitly.

Note that the default IP address, 127.0.0.1, is not accessible from other machines on your network. To make your development server viewable to other machines on the network, use its own IP address (e.g. 192.168.2.1) or 0.0.0.0 or :: (with IPv6 enabled).

Optional arguments:

  -?, --help
      show this help message and exit
  -h HOST, --host HOST
      server host
  -p PORT, --port PORT
      server port
  --threaded
      Use it to start the development server is multithreaded mode.
  --processes PROCESSES
      defines number of processes
  --passthrough-errors
      disable the error catching. This means that the server will die on errors but it can be useful to hook debuggers in (pdb etc.)
  -d, --debug
      enables the Werkzeug debugger (DO NOT use in production code)
  -D, --no-debug
      disables the Werkzeug debugger
  -r, --reload
      Use it to monitor Python files for changes (default)
  -R, --no-reload
      Use the --noreload option to disable the use of the auto-reloader. This means any Python code changes you make while the server is running will not take effect if the particular Python modules have already been loaded into memory.

Shell
-----

.. code-block:: console

  python manage.py shell [-?] [--no-ipython] [--no-bpython]

Runs a Python shell inside Flask application context.

optional arguments:

  --no-bpython
      do not use the IPython shell
  --no-ipython
      do not use the BPython shell

.. note::

  Following variables would be available in the console:
    * app - Flask application object
    * db - SqlAlchemy database
    * models - all defined SqlAlchemy models in the project

Database-related commands
=========================

Create Db Tables
----------------

Usage:

.. code-block:: console

  python manage.py create_db_tables

Creates Postgres db tables

Drop Db Tables
--------------

Usage:

.. code-block:: console

  python manage.py drop_db_tables

Drops Postgres db tables

Create DynamoDB tables
----------------------

Usage:

.. code-block:: console

  python manage.py create_dynamodb_tables

Creates tables in DynamoDB

Db
--

Usage:

.. code-block:: console

  python manage.py db [positional arguments]

Performs database migrations

Positional arguments:
 
* `upgrade`
    Upgrade to a later version
* `branches`
    Lists revisions that have broken the source tree into two versions representing two independent sets of changes
* `migrate`
    Alias for 'revision --autogenerate'
* `current`
    Display the current revision for each database.
* `stamp`
    'stamp' the revision table with the given revision; don't run any migrations
* `init`
    Generates a new migration
* `downgrade`
    Revert to a previous version
* `history`
    List changeset scripts in chronological order.
* `revision`
    Create a new revision file.


.. note::

  As background implementation is `Alembic package <https://alembic.readthedocs.org/>`_ is used.


Celery-related commands
=======================

celeryd
-------

Usage: 

.. code-block:: console

  python manage.py celeryd [-?]

Runs the default Celery worker node.

flower
------

Usage: 

.. code-block:: console

  python manage.py flower [-?]

Runs the Celery Flower is a real-time web based monitor and administration tool for Celery.

celeryw
-------

Usage:

.. code-block:: console

  python manage.py celeryw [-?]

Runs another Celery worker node.

Create Amazon EC2 instance's image
----------------------------------

Usage: 

.. code-block:: console

  python manage.py create_image [-?] [-v VERSION]

Creates Amazon EC2 instance with preinstalled Cloudml celery worker to use it in the spot instance.

Optional arguments:
  -v VERSION, --version VERSION
      For example cloudml-worker.v3.0

Creates Amazon EC2 instance's image with preinstalled Cloudml celery worker to use it in the spot instance.

Unittests-related commands
==========================

Test
----

Usage:

.. code-block:: console

  python manage.py test [-?] [-t TESTS] [-c]

Runs API unittests.

Optional arguments:

  -t TESTS, --tests TESTS
                        specifies unittests to run
  -c, --coverage        runs API part unittest with coverage

.. note::

  Before running tests please create test_config.py file in the `api` folder of the project. Use `test_config.py.tpl` as the sample.

If you running tests with coverage, you could find html report in `coverage` folder.

.. note::

  Now coverage starts the monitoring after importing all model, view, etc. classes declaration. So those string would not included to the report. To avoid this you could use following command for running nosetests with coverage:

  .. code-block:: console

    nosetests api --verbose --with-coverage --cover-erase --cover-html --cover-package=api --cover-html-dir=coverage

You could run only one specific test, using -t argument.
For example:

.. code-block:: console

  python manage.py test -tests api.import_handlers.tests:DataSetsTests.test_details
