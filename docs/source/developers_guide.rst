=================
Developer's guide
=================

.. contents:: 
   :depth: 4

Ubuntu bootstrap
================

-------
Backend
-------

Installation
------------

Install system requirement:

.. code-block:: console

    $ sudo apt-get install liblapack-dev gfortran libpq-dev libevent-dev python-dev rabbitmq-server

Create virtual env:

.. code-block:: console

    $ virtualenv --no-site-packages ve
    $ . ve/bin/activate

.. note::

  It would be better, if you have pip version 1.1.


Install numpy and scipy:

.. code-block:: console

    $ export LAPACK=/usr/lib/liblapack.so
    $ export ATLAS=/usr/lib/libatlas.so
    $ export BLAS=/usr/lib/libblas.so
    $ pip install numpy==1.7.1
    $ pip install scipy==0.12.0

Install python requirements:

.. code-block:: console

    $ pip install -r ./requirements.txt

.. note::

    To use your local version of cloudml, instead of the one coming from requirements.txt of cloudml-ui project:

    - pip uninstall cloudml
    - let PYTHONPATH point to your cloudml root directory


Install Postgresql using `the instruction <https://help.ubuntu.com/community/PostgreSQL>`_. Version should be more, than 9.2.

.. code-block:: console

    $ sudo bash -c "echo 'deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main' >> /etc/apt/sources.list.d/pgdg.list"
    $ wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
    $ sudo apt-get update
    $ sudo apt-get install -y postgresql-9.3
    

Create user and database:

.. code-block:: console

    $ sudo -u postgres psql -c "CREATE USER cloudml WITH PASSWORD 'cloudml';"
    $ sudo -u postgres createdb -O cloudml cloudml

.. note::
  
  Need set password to 'cloudml' for default setting.

Create local config:

.. code-block:: console

    $ cp api/local_config.py.tpl api/local_config.py

Create OATH API keys using on `Upwork <https://www.upwork.com/services/api/apply>`_. Callback URL is http://127.0.0.1:3333/#/auth/callback and fill local_config.py:

.. code-block:: console

    $ ODESK_OAUTH_KEY = '{{ odesk api key }}'
    $ ODESK_OAUTH_SECRET = '{{ odesk secret key }}'

Configure rabbitmq(celery broker):

.. code-block:: console

    $ rabbitmqctl add_user cloudml cloudml
    $ rabbitmqctl add_vhost cloudml
    $ rabbitmqctl set_permissions cloudml cloudml "*" "*" "*
    "

To install nltk/punkt you need to hid to `the page <http://www.nltk.org/data.html>`_ and follow the direction. After nltk.download() choose to download punkt. 

Install local dynamodb from `Amazon's DynamoDB Local page <http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Tools.DynamoDBLocal.html>`_.

Run local dynamodb:

.. code-block:: console
    
    $ ./api/logs/dynamodb/dynamodb_local.sh

Create dynamodb tables:

.. code-block:: console

    $ python manage.py create_dynamodb_tables

Create postgresql tables:

.. code-block:: console

    $ python manage.py create_db_tables

Running the server
------------------

Run dev server:

.. code-block:: console

    $ python manage.py runserver --threaded

.. note::

  Don't forgot to run local dynamodb:

    .. code-block:: console
        
        $ ./api/logs/dynamodb/dynamodb_local.sh

Run shell:

.. code-block:: console

    $ python manage.py shell

.. _celery:

Running Celery
--------------

Run celery:

.. code-block:: console

    $ python manage.py celeryd

Run flower (celery monitor):

.. code-block:: console

    $ python manage.py flower

Unittests
---------

Run tests:

.. code-block:: console

    $ python manage.py test

Check unittests coverage:

.. code-block:: console

    $ nosetests --with-coverage --cover-package=api.accounts --verbose --tests api.accounts.tests --cover-html-dir=coverage --cover-html

--------
Frontend
--------

We are trying to maintain a minimal number of global node modules. In a perfect configuration you should only have the following modules in ``/usr/local/lib/node_modules``:

-  bower
-  coffee-script
-  grunt-cli
-  npm

.. note::

  This is on as-needed-basis, if you are missing a global dependency do the following, you will usually need ``sudo``:

    .. code-block:: console

       $ sudo npm install -g bower@1.3.9
       $ sudo npm install -g coffee-script@1.8.0
       $ sudo npm install -g grunt-cli@0.1.13

Installation
------------

Installing node and npm
~~~~~~~~~~~~~~~~~~~~~~~

Downloading and install nvm:

.. code-block:: console

  $ curl https://raw.githubusercontent.com/creationix/nvm/v0.11.1/install.sh | bash
  $ source ~/.profile

Installing node 0.10.28:

.. code-block:: console

  $ nvm ls-remote
  $ nvm install 0.10.28
  $ nvm alias default 0.10.28


Installing node and bower modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Change directory to your local cloudml-ui/ui directory and do the following:

.. code-block:: console

   $ rm -r node_modules bower_components
   $ npm cache clean
   $ npm install
   $ bower cache clean
   $ bower install

Building 3rd party
~~~~~~~~~~~~~~~~~~

Not all third party requires building, only few and declining.

Building x-editable

version 1.4.4 of x-editable doesn't yet come with pre-build
redistributable so you have to build it yourself.

Change directory to your local cloudml-ui/ui directory and do the following:

.. code-block:: console

   $ cd bower_components/x-editable
   $ npm install
   $ grunt build

Now you have ``bower_components/x-editable/dist`` directory to serve x-editable locally, note that x-editable on production is served through CDN.

Updating Webdrive
~~~~~~~~~~~~~~~~~

Change directory to your local cloudml-ui/ui directory.

Update webdrive to install chrome driver and selenium standalone server:

.. code-block:: console

   $ ./node_modules/protractor/bin/webdriver-manager update

in case webdrive updates fails for any reason, do the follwoing are retry the update:

.. code-block:: console

   $ rm -r ./node_modules/protractor/selenium

Grunt Key Tasks
---------------

Change directory to your local cloudml-ui/ui directory:

.. code-block:: console

   $ grunt --help

This will display grunt available tasks, generally use this when needed.

Running the app during development (grunt server)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ grunt server

This will run the application and monitors key files for live reload.

You can also do:

.. code-block:: console

   $ grunt server:usecdn

If you want to run against CDN version of 3rd parties. By default ``grunt server`` will run against local 3rd parties files for speed (look at ./vendor.config.coffee for more details on this)


Building \_public
~~~~~~~~~~~~~~~~~

.. code-block:: console

   $ grunt build

This will build the distributable files. It will include
./app/scripts/prod\_config.coffee by default. You can use staging by grunt build:staging, further more you can try out the built files locally by using grunt build:local and launch a simple server against \_public like:

.. code-block:: console

   $ cd _public
   $ python -m SimpleHTTPServer 8080


Frotend Tests
-------------

Unittests
~~~~~~~~~

.. code-block:: console

   $ grunt unit

This should launch a browser/chrome and run the frontend unit tests.

Coverage
~~~~~~~~

.. code-block:: console

   $ grunt coverage

Then open ./coverage/xyz/index.html in browser

E2E with Protractor (grunt e2e)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Launch local frontend server:

.. code-block:: console

   $ grunt server

Launch E2E tests:

.. code-block:: console

   $ grunt e2e

This should launch a browser/chrome and run the E2E tests.

.. note::

  Make sure you are running your local backend.


The role of vendor.config.coffee
--------------------------------

The file vendor.config.coffee is centralized place to reference
vendor/3rd party bower libraries. Currently it works with JS files only.
Vendor/3rd party CSS files are still added manually in
app/assets/index.html. At some point of time we will extend
vendor.config.coffee to deal with CSS files (vendor.css and CDN
serving), but that on as needed basis.

It should also be noted that, karma will use vendor.config.coffee to
build the test environment so all your tests will include the same 3rd party libraries that is used in development and production.

Generally all files referenced will be processed in the same order they appear int vendor.config.coffee, and some libraries need special care in ordering, like angular before angular-route.

vendor.config.coffee contains 2 sections as follow:

CDN Section
~~~~~~~~~~~

This is for 3rd party JS that should be served from CDN on production. It is a list of objects, each containing:

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
    When adding a file in vendor.config.coffee watch out for coffee script indentations it should be as follows and notice the indentation of external key after the comma:

    .. code-block:: console

      coffee-script     ,       external:         "https://cdn/lib/lib.min.js"       notmin:         "https://cdn/lib/lib.js"       local:         "bower_components/lib/lib.js"

Bundled Section
~~~~~~~~~~~~~~~

If you don't wish to serve 3rd party library over CDN, like in case
there is not HTTPS CDN for the library, or it is not being served over
CDN, etc. You put the bower path of the library in the bundled section.
These files will concat and uglified in production in a file called
vendor.js.


MacOS bootstrap
===================

The following section describes the installation of cloudml-ui on MacOS.

-------
Backend
-------

Create virtual env:

.. code-block:: console

  $ virtualenv --no-site-packages ve
  $ . ve/bin/activate

Install numpy and scipy:

.. code-block:: console

  $ export LAPACK=/usr/lib/liblapack.so
  $ export ATLAS=/usr/lib/libatlas.so
  $ export BLAS=/usr/lib/libblas.so
  $ pip install numpy==1.7.1
  $ pip install scipy==0.12.0

Install python requirements:

.. code-block:: console

  $ pip install -r ./requirements.txt


Downgrade psycopg2 (if not already set to this version):

.. code-block:: console

  $ pip install -U psycopg2==2.4.6

Create local config:

.. code-block:: console

  $ cp api/local_config.py.tpl api/local_config.py

.. note:: 

  Create OATH API keys using `Upwork <https://www.odesk.com/services/api/apply>`_. Callback URL is http://127.0.0.1:3333/#/auth/callback


Install rabbit mq:

.. code-block:: console

  $ brew install rabbitmq

Start rabbit mq:

.. code-block:: console

  $ rabbitmq-server -detached

Configure rabbitmq(celery broker):

.. code-block:: console

  $ rabbitmqctl add_user cloudml {{password}}
  $ rabbitmqctl add_vhost cloudml
  $ rabbitmqctl set_permissions cloudml cloudml ".*" ".*" ".*"


Download dynamodb and install it. Configure it as follows:

.. code-block:: console

  $ edit cloudml-ui/api/logs/dynamodb/dynamodb_local.sh 
  $ set  -Djava.library.path to your installation's DynamoDBLocal_lib directory
  $ set -jar to your installation's DynamoDBLocal.jar

Start local dynamodb:

.. code-block:: console

  $ cloudml-ui/api/logs/dynamodb/dynamodb_local.sh &

Install postgres:

.. code-block:: console

  $ brew install postgresql

Start postgres:

.. code-block:: console

  $ pg_ctl -D /usr/local/var/postgres -l

Create database, users and roles in postgres:

.. code-block:: console

  $ psql -d template1
  psql (9.4.4)
  Type "help" for help.

  template1=# create user cloudml with password 'cloudml';
  CREATE ROLE
  template1=# create database cloudml;
  CREATE DATABASE
  template1=# grant all privileges on database cloudml to cloudml;
  GRANT
  template1=# \q


Tornado:

.. code-block:: console

  $ pip uninstall tornado (4.x) because of missing import in celery, tornado.auth.GoogleMixin from celery.
  $ pip install tornado==2.3
  
Celery:

.. code-block:: console

  $ pip install celery 
  $ pip show -f celery
  ---
  Metadata-Version: 2.0
  Name: celery
  Version: 3.1.18
  Summary: Distributed Task Queue
  Home-page: http://celeryproject.org
  Author: Ask Solem
  Author-email: ask@celeryproject.org
  License: BSD
  Location: /opt/local/Library/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages
  Requires: pytz, billiard, kombu
  Files:
    ../../../bin/celery
    ../../../bin/celerybeat
    ../../../bin/celeryd
    ../../../bin/celeryd-multi
  $ So set your path to  /opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/
  $ which celery
  /opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin/celery
  
Start all cloudml-ui backend servers. These have to be started from inside the cloduml-ui directory:

.. code-block:: console

  $ python manage.py runserver
  $ python manage.py celeryd
  (Dont run the first two above in backend. Open a seperate console tab/window and run them.)
  $ Dyanmodb (./api/logs/dynamodb/dynamodb_local.sh &) 
  $ rabbitmq (rabbitmq-server -detached ) (Detached runs in background.)

--------
Frontend
--------

Installation
------------

Install the following modules as follows:

.. code-block:: console

  cloudml-ui $ brew install nodejs
  cloudml-ui $ brew install npm
  cloudml-ui $ sudo npm install grunt-cli -g
  $ npm install -g bower 

  Just run bower install under cloudml-ui/ui directory. There is a bower.json there.
  Chose the lower version of angular js or something like this !1 while doing bower install.
  Unable to find a suitable version for angular, please choose one:
    1) angular#1.2.19 which resolved to 1.2.19 and is required by angular-mocks#1.2.19
    2) angular#1.2.20 which resolved to 1.2.20 and is required by angular-cookies#1.2.20, angular-mocks#1.2.20, angular-resource#1.2.20, angular-route#1.2.20, angular-sanitize#1.2.20, cloudml-ui-frontend
  Unable to find a suitable version for codemirror, please choose one:
    1) codemirror#4.3 which resolved to 4.3.0 and is required by angular-ui-codemirror#0.1.7
    2) codemirror#4.5.0 which resolved to 4.5.0 and is required by cloudml-ui-frontend

  Prefix the choice with ! to persist it to bower.json

  ? Answer: !1
  
Global modules installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Make sure the following are installed:

.. code-block:: console

  $ sudo npm install -g bower@1.3.9
  $ sudo npm install -g coffee-script@1.8.0
  $ sudo npm install -g grunt-cli@0.1.13

Change directory to your local cloudml-ui/ui directory and do the following:

.. code-block:: console

  $ rm -r node_modules bower_components
  $ npm cache clean
  $ npm install
  $ bower cache clean
  $ bower install

Building x-editable
~~~~~~~~~~~~~~~~~~~

Version 1.4.4 of x-editable doesn't yet come with pre-build redistributable so you have to build it yourself.

Change directory to your local cloudml-ui/ui directory and do the following:

.. code-block:: console

  cd bower_components/x-editable

  npm install

  grunt build
  
  Ignore this initial error 
  Loading "test.js" tasks and helpers...ERROR
  >> Error: No such module: evals

  In the end grunt build command should output,
  Done, without errors.

  Now you have bower_components/x-editable/dist directory to serve x-editable locally, note that x-editable on production is served through CDN.

Run npm install under ui directory as well:

.. code-block:: console

  cd ui
  
  npm install  
  
  Ignore these errors:
  make: *** [Release/obj.target/fse/fsevents.o] Error 1
  gyp ERR! build error
  gyp ERR! stack Error: `make` failed with exit code: 2
  gyp ERR! stack    at ChildProcess.onExit (/usr/local/lib/node_modules/npm/node_modules/node-gyp/lib/build.js:269:23)
  
  As long as you get these installation messages like this, this step has run fine:
  karma@0.12.37 node_modules/karma
  ├── di@0.0.1
  ├── graceful-fs@3.0.8
  ├── mime@1.3.4
  ├── colors@1.1.2
  
Updating Webdrive
~~~~~~~~~~~~~~~~~

Change directory to your local cloudml-ui/ui directory

Update webdrive to install chrome driver and selenium standalone server

.. code-block:: console

  ./node_modules/protractor/bin/webdriver-manager update

in case webdrive updates fails for any reason, do the follwoing are retry the update

.. code-block:: console

  rm -r ./node_modules/protractor/selenium

Grunt Key Tasks and Testing your installation
---------------------------------------------

Change directory to your local cloudml-ui/ui directory:

.. code-block:: console

  grunt --help

This will display grunt available tasks, generally use this when needed.

Unit Tests (grunt unit)

.. code-block:: console

  grunt unit

This should launch a browser/chrome and run the unit tests.

Starting front-end server
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

  $ grunt server

.. note::

  Dont run the above in backend. Open a seperate tab/window and run it since you would want to see the messages on the console.

In case you get the following error, do the following:

.. code-block:: console
  
  SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:59
  
So we looked at this http://stackoverflow.com/questions/28115250/boto-ssl-certificate-verify-failed-certificate-verify-failed-while-connecting. And resolved it this way.
  
In  cloudml-ui/api/amazon_utils/__init__.py, class AmazonS3Helper, def __init__ method,in the last line, we passed one additional parameter, is_secure=False to boto.connect_s3 method, as shown below:

.. code-block:: python

   67 class AmazonS3Helper(object):
   68     def __init__(self, token=None, secret=None, bucket_name=None):
   69         token = token or app.config['AMAZON_ACCESS_TOKEN']
   70         secret = secret or app.config['AMAZON_TOKEN_SECRET']
   71         self.bucket_name = bucket_name or app.config['AMAZON_BUCKET_NAME']
   72         self.conn = boto.connect_s3(token, secret,is_secure=False)  


Vagrant
=======

Before diving into cloudml, please `install the latest version of Vagrant <http://docs.vagrantup.com/v2/installation/>`_. And because we'll be using `VirtualBox <http://www.virtualbox.org/>`_ as our provider for the getting started guide, please install that as well.

Clone cloduml repo:

.. code-block:: console

  $ git clone https://github.com/odeskdataproducts/cloudml.git

For boot your Vagrant environment. Run the following:

.. code-block:: console

  $ cd cloudml-ui
  $ vagrant up

In 20-30 minutes, this command will finish and you'll have a virtual machine running Ubuntu with installed all dependencies.

For connect to machine run:

.. code-block:: console

  $ vagrant ssh

For run test please go to `/vagrant` directory:

.. code-block:: console

  $ cd /vagrant
  $ python setup.py test

When you're done fiddling around with the machine, run `vagrant destroy` back on your host machine, and Vagrant will remove all traces of the virtual machine.

A `vagrant suspend` effectively saves the exact point-in-time state of the machine, so that when you resume it later, it begins running immediately from that point, rather than doing a full boot.


Installing test data
====================

Please download archive with test dataset :download:`dump.tar.gz <_static/dump.tar.gz>` and decompress it:

.. code-block:: console

  $ tar -zxvf dump.tar.gz

Run postgres client:

.. code-block:: console

  $ psql -s cloudml

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

.. note::

    The above dump file is found in cloudml-ui directory. Better to put this dump file into a folder with no spaces in its path name. Otherwise it was not working.
    
    Grant all permissions to table ja_quick_info for user cloudml::

      cloudml=# grant all privileges on table ja_quick_info  to cloudml;
    
Now login as cloudml user and check. The below select should work:

.. code-block:: console

  $ psql -s cloudml -U cloudml
  psql (9.4.4)
  Type "help" for help.

  cloudml=> select * from ja_quick_info limit 1;
  ***(Single step mode: verify command)*******************************************
  select * from ja_quick_info limit 1;
  ***(press return to proceed or enter x and return to cancel)********************

  cloudml=> \q

The above select statement should NOT give a permission-denied message like this::

  $ psql -s cloudml -U cloudml
  psql (9.4.4)
  Type "help" for help.

  cloudml=> select * from ja_quick_info limit 1;
  ***(Single step mode: verify command)*******************************************
  select * from ja_quick_info limit 1;
  ***(press return to proceed or enter x and return to cancel)********************

  ERROR:  permission denied for relation ja_quick_info
  cloudml=> \q  


Build docs
==========

For build docs please install:

.. code-block:: console

    $ sudo pip install Sphinx==1.3.1

Build html doc:

.. code-block:: console

  $ cd doc
  $ make html

View doc in ./doc/_build/html directory.