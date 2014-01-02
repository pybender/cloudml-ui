Cloudml UI
==========

Development
-----------

Create virtual env and install requirements::

    $ virtualenv --no-site-packages ve
    $ . ve/bin/activate
    $ pip install -r requirements.txt

Run dev server::

    $ python manage.py runserver

Run tests::

	$ python manage.py test

	$ nosetests --tests api.test.test_features


Ssh tonel:

	$ ssh -D localhost:12345 nmelnik@172.27.67.106