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

Run dev server::

    $ python manage.py runserver

Run celery::

    $ python manage.py celeryd

Run flower (celery monitor)::

    $ python manage.py flower

Run shell::

    $ python manage.py shell


Frontend
--------

Install nodejs and nmp(nodejs==0.8.6)::

    $ sudo apt-get install nodejs npm

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