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

    or

    export CLOUDML_CONFIG="{{ path to }}/cloudml-ui/api/test_config.py"
    nosetests --tests api.test.test_features
