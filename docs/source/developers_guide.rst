=================
Developer's guide
=================

Ubuntu
======

-------
Backend
-------

Install system requirement::

    $ sudo apt-get install liblapack-dev gfortran libpq-dev libevent-dev python-dev rabbitmq-server

Create virtual env::

    $ virtualenv --no-site-packages ve
    $ . ve/bin/activate

.. note::
  It would be better, if you have pip version 1.1.

Install numpy and scipy::

    $ export LAPACK=/usr/lib/liblapack.so
    $ export ATLAS=/usr/lib/libatlas.so
    $ export BLAS=/usr/lib/libblas.so
    $ pip install numpy==1.7.1
    $ pip install scipy==0.12.0

Install python requirements::

    $ pip install -r ./requirements.txt

.. note::
    To use your local version of cloudml, instead of the one coming from requirements.txt of cloudml-ui project:

    - pip uninstall cloudml
    - let PYTHONPATH point to your cloudml root directory

Install Postgresql using instruction https://help.ubuntu.com/community/PostgreSQL

Create user and database::

    $ sudo -u postgres createuser -D -A -P cloudml
    $ sudo -u postgres createdb -O cloudml cloudml

.. note::  Need set password to 'cloudml' for default setting.

Create local config::

    $ cp api/local_config.py.tpl api/local_config.py

Create OATH API keys using https://www.upwork.com/services/api/apply. Callback URL is http://127.0.0.1:3333/#/auth/callback and fill local_config.py::

    $ ODESK_OAUTH_KEY = '{{ odesk api key }}'
    $ ODESK_OAUTH_SECRET = '{{ odesk secret key }}'

Configure rabbitmq(celery broker)::

    $ rabbitmqctl add_user cloudml cloudml
    $ rabbitmqctl add_vhost cloudml
    $ rabbitmqctl set_permissions cloudml cloudml "*" "*" "*
    "

To install nltk/punkt you need to hid to http://www.nltk.org/data.html and follow
the direction. After nltk.download() choose to download punkt. 

Run local dynamodb::
    
    $ ./api/logs/dynamodb/dynamodb_local.sh

Create dynoamodb tables::

    $ python manage.py create_dynamodb_tables

Create postgresql tables::

    $ python manage.py create_db_tables

Run dev server::

    $ python manage.py runserver --threaded

.. _celery:

Run celery::

    $ python manage.py celeryd

Run flower (celery monitor)::

    $ python manage.py flower

Run shell::

    $ python manage.py shell

Run tests::

    $ python manage.py test

Check unittests coverage::

    $ nosetests --with-coverage --cover-package=api.accounts --verbose --tests api.accounts.tests --cover-html-dir=coverage --cover-html

--------
Frontend
--------


Installation Strategy
---------------------

We are trying to maintain a minimal number of global node modules. In a
perfect configuration you should only have the following modules in
``/usr/local/lib/node_modules``

-  bower
-  coffee-script
-  grunt-cli
-  npm

Global Modules Installation
---------------------------

This is on as-needed-basis, if you are missing a global dependency
listed in the `Installation Strategy <#installation-strategy>`_ do the
following, you will usually need ``sudo``::

   $ sudo npm install -g bower@1.3.9
   $ sudo npm install -g coffee-script@1.8.0
   $ sudo npm install -g grunt-cli@0.1.13

Installation
------------

Change directory to your local cloudml-ui/ui directory and do the
following::

   $ rm -r node_modules bower_components
   $ npm cache clean
   $ npm install
   $ bower cache clean
   $ bower install

Building 3rd party
------------------

Not all third party requires building, only few and declining.

Building x-editable
~~~~~~~~~~~~~~~~~~~

version 1.4.4 of x-editable doesn't yet come with pre-build
redistributable so you have to build it yourself.

Change directory to your local cloudml-ui/ui directory and do the
following:

   $ cd bower_components/x-editable
   $ npm install
   $ grunt build

Now you have ``bower_components/x-editable/dist`` directory to serve
x-editable locally, note that x-editable on production is served through
CDN.

Updating Webdrive
-----------------

Change directory to your local cloudml-ui/ui directory

Update webdrive to install chrome driver and selenium standalone server

   $ ./node_modules/protractor/bin/webdriver-manager update

in case webdrive updates fails for any reason, do the follwoing are
retry the update

   $ rm -r ./node_modules/protractor/selenium

Grunt Key Tasks and Testing your installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Change directory to your local cloudml-ui/ui directory

   $ grunt --help

This will display grunt available tasks, generally use this when needed.

Unit Tests (grunt unit)
^^^^^^^^^^^^^^^^^^^^^^^

   $ grunt unit

This should launch a browser/chrome and run the unit tests. It *should*
all pass :), when done do ``CTRL+C``

E2E with Protractor (grunt e2e)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Make sure you are running your local backend**

Launch local frontend server::

   $ grunt server

Launch E2E tests::

   $ grunt e2e

This should launch a browser/chrome and run the E2E tests. It *should*
all pass :)

Running the app during development (grunt server)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

   $ grunt server

This will run the application and monitors key files for live reload.

You can also do::

   $ grunt server:usecdn

If you want to run against CDN version of 3rd parties. By default
``grunt server`` will run against local 3rd parties files for speed
(look at ./vendor.config.coffee for more details on this)

Building \_public
^^^^^^^^^^^^^^^^^

   $ grunt build

This will build the distributable files. It will include
./app/scripts/prod\_config.coffee by default. You can use staging by
grunt build:staging, further more you can try out the built files
locally by using grunt build:local and launch a simple server against
\_public like::

   $ cd _public
   $ python -m SimpleHTTPServer 8080

Coverage
^^^^^^^^

   $ grunt coverage

Then open ./coverage/xyz/index.html in browser

The role of vendor.config.coffee
--------------------------------

The file vendor.config.coffee is centralized place to reference
vendor/3rd party bower libraries. Currently it works with JS files only.
Vendor/3rd party CSS files are still added manually in
app/assets/index.html. At some point of time we will extend
vendor.config.coffee to deal with CSS files (vendor.css and CDN
serving), but that on as needed basis.

It should also be noted that, karma will use vendor.config.coffee to
build the test environment so all your tests will include the same 3rd
party libraries that is used in development and production.

Generally all files referenced will be processed in the same order they
appear int vendor.config.coffee, and some libraries need special care in
ordering, like angular before angular-route.

vendor.config.coffee contains 2 sections as follow:

CDN Section
~~~~~~~~~~~

This is for 3rd party JS that should be served from CDN on production.
It is a list of objects, each containing:

-  **external**: The CDN url of the library, minified as it should be
   served in production. This form is used using grunt build. You should
   use https:// to serve 3rd parties **and refrain from using any CDN
   for any library that is not served over CDN to avoid and script
   injection attacks**
-  **notmin**: The CDN url of the library, nonminified, used create
   special builds for debugging purposes using grunt server:usecdn
-  **local**: The local path the library like
   'bower\_components/lib/somehting.js', this will be used generally in
   development using grunt server, also it will be used by karma to
   construct the test environment.

.. note::
    When adding a file in vendor.config.coffee watch out for coffee script indentations it should be as follows and notice the indentation of external key after the comma::

    ``coffee-script     ,       external:         "https://cdn/lib/lib.min.js"       notmin:         "https://cdn/lib/lib.js"       local:         "bower_components/lib/lib.js"``

Bundled Section
~~~~~~~~~~~~~~~

If you don't wish to serve 3rd party library over CDN, like in case
there is not HTTPS CDN for the library, or it is not being served over
CDN, etc. You put the bower path of the library in the bundled section.
These files will concat and uglified in production in a file called
vendor.js.

Mac Os
======


Vagrant
=======


Installing test data
====================

Please download archive with test dataset :download:`dump.tar.gz <_static/dump.tar.gz>` and decompress it::

  $ tar -zxvf dump.tar.gz

Create db table:

.. code-block:: sql

  CREATE TABLE ja_quick_info (
  application bigint,
  opening bigint,
  employer_info text,
  agency_info text,
  contractor_info text,
  file_provenance character varying(256),
  file_provenance_date date
  );

Fill data from dump.csv:

.. code-block:: sql

  COPY ja_quick_info FROM 'path_to_dump/dump.csv' CSV HEADER;
