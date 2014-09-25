Development
===========

Backend
-------

Install system requirements(mongodb==2.4.6)::

    $ sudo apt-get install liblapack-dev gfortran libpq-dev libevent-dev python-dev mongo-server

Create virtual env::

    $ virtualenv --no-site-packages ve
    $ . ve/bin/activate

Install numpy and scipy::

    $ export LAPACK=/usr/lib/liblapack.so
    $ export ATLAS=/usr/lib/libatlas.so
    $ export BLAS=/usr/lib/libblas.so
    $ pip install numpy
    $ pip install scipy

Install python requirements::

    $ pip install -r requirements.txt

Create local config::

    $ cp api/local_config.py.tpl api/local_config.py

Note::

    Create OATH API keys using https://www.odesk.com/services/api/apply. Callback URL is http://127.0.0.1:3333/#/auth/callback

Configure rabbitmq(celery broker)::

    $ rabbitmqctl add_user cloudml {{password}}
    $ rabbitmqctl add_vhost cloudml
    $ rabbitmqctl set_permissions cloudml cloudml "*" "*" "*
    "
Run local dynamodb::
    
    $ ./api/logs/dynamodb/dynamodb_local.sh

Run dev server::

    $ python manage.py runserver

.. _celery:

Run celery::

    $ python manage.py celeryd

Run flower (celery monitor)::

    $ python manage.py flower

Run shell::

    $ python manage.py shell

Check unittests coverage:

    $ nosetests --with-coverage --cover-package=api.accounts --verbose --tests api.accounts.tests --cover-html-dir=coverage --cover-html

Frontend
--------

Install nodejs and nmp(nodejs==0.8.6)::

    $ sudo apt-get install nodejs npm

Install grunt-cli globally

    $ sudo npm install grunt-cli -g

Install bower dependencies

    $ bower install

Init ui dev enviropment::
    
    $ cd ui
    $ ./scripts/init.sh

Run ui dev server::

    $ cd ui
    $ ./scripts/server.sh

Cloudml *CORE*
--------------

If you use pip install -r requirements.txt to set up your development environment
as described above, you wouldn't need to do much to setup your environment for the 
core Cloudml. But just in case

Install requirements

    $ pip install requirements.txt

To install nltk/punkt you need to hid to http://www.nltk.org/data.html and follow
the direction. After nltk.download() choose to download punkt. 

Testing cloudml

    $ nosetests

To use your local version of cloudml, instead of the one coming from requirements.txt
of cloudml-ui project:

1. pip uninstall cloudml
2. let PYTHONPATH point to your cloudml root directory

Training Your First Model
-------------------------

**Prepare Default Instance:** Go to instances, click "Add new AWS instance", 
name it **default**, otherwise rabbitmq/celery wouldn't pick training and testing
tasks, in the IP use 127.0.0.1, in the type choose small.
Finally make sure **Is Default?** checkbox is checked.

**Create JSON import handler:** Go to import handlers/json, "Add new import handler",
give it a name, choose the file **extract.json** from cloudml-ui/conf directory. After 
creation look for the "Data Sources" section of the just created import handler, and
edit it to reflect where the table called **ja_quick_info** resides. You will also
need to populate that table, so **ask** any team member to give you a dump of that table.
Now **Run Query** on that import handler. When asked for start/end use 2012-12-03 and 2012-12-04 respectively. 
Now you should get couple of rows to make sure your import handler configuration is good.

**Import Data Set:** You need to make sure that celeryd is running as indicated in celery_.
Then in the import handler you've just created, click "Import DataSet", for start/end 
use 2012-12-03 and 2012-12-04 respectively. Now click "Logs", you should see some logs with no 
errors. Go to "Details" you should see "Records Count" to be 99.

**Create & Train a Model:** Go to models, and click "Add New Model", give it a name,
and use the file cloudml-ui/conf/features.json and the import handler you've just created.
After adding the model, click "Start Training", select the dataset you imported in previous step,
and the default instance should be created by default. Now click "Start Training". 
Navigate back to models to refresh the status of the models. You should now see that your
created model is **Trained**.

**Congratulations You have Trained your FIRST model**


