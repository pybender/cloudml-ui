Cloudml UI
==========

Development Backend/API
=======================

Create virtual env and install requirements::

    $ virtualenv --no-site-packages ve
    $ . ve/bin/activate

Install numpy and scipy::

    $ export LAPACK=/usr/lib/liblapack.so
    $ export ATLAS=/usr/lib/libatlas.so
    $ export BLAS=/usr/lib/libblas.so
    $ pip install numpy
    $ pip install scipy

Install requirements::

    $ pip install -r requirements.txt

SSH tunnel:

	$ ssh -D localhost:12345 nmelnik@172.27.67.106

* You will also need to change api/local_config.py, api/test_config.py and api/config.py to match your local configuration.

* You can use AWS credentials in local_config.py giving that you will use your own buckets.

* For RabbitMQ (see later), you will need to make sure that it is running on port 5672 (the default port number has changed lately)

Third Party Requirements
------------------------

1. PostgreSQL 9.2 or later
2. mongodb
3. RabbitMQ

Running Backend/API & Tests
---------------------------
Now you can check your installation, activate your virtual env if not already.

Run dev server::

    $ python manage.py runserver

Run tests::

    $ python manage.py test

    $ nosetests --tests api.test.test_features


Development Frontend
====================

Install required NodeJS packages::

    $ cd ui
    $ npm install

You can also learn more about the front end from ui/README.md