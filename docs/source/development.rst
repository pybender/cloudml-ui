Development
===========

Backend
-------

Create virtual env and install requirements::

    $ virtualenv --no-site-packages ve
    $ . ve/bin/activate
    $ pip install -r requirements.txt

Create local config::

    $ cp api/local_config.py.tpl api/local_config.py

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

Install nodejs and nmp::

    $ sudo apt-get install nodejs npm

Init ui dev enviropment::
    
    $ cd ui
    $ ./scripts/init.sh

Run ui dev server::

    $ cd ui
    $ ./scripts/server.sh
