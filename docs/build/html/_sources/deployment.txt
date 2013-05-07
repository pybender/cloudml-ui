Deployment
==========

Setup project to new instance
-----------------------------

We are going to deploy using:

- Apache
- Fabdeploy
- Virtualenv
- Supervisor
- EC2 instance with Ubuntu

Create virtual env locally::

    $ virtualenv --no-site-packages ve
    $ . ve/bin/activate
    $ pip install -r requirements.txt

Create settings::

    $ cp fabconf.py.def fabconf.py

Add new configuration. For example::

    class StagingConf(BaseConf):
        """Settings specific to staging environment."""
        # user@ip_address
        address = 'cloudml@172.27.67.106'

        sudo_user = 'nmelnik'
        home_path = '/webapps/cloudml'

        # Code from this branch will be deployed.
        branch = 'staging'

        server_name = 'cloudml.staging.match.odesk.com'
        # For Apache ServerAdmin directive
        server_admin = 'nmelnik@odesk.com'
        # Apache will serve WSGI on this port.
        apache_port = 5000

        # It should be a Jinja2 template, and can make use of fabdeploy config
        # variables.
        remote_settings_lfile = 'staging_config.py.tpl'


Read fabfile.py tasks to be aware of changes that will be made to your system.

Install packages, create user::

    $ fab staging install

Setup software::

    $ fab staging setup

Deploy current version::

    $ fab staging deploy

For first starting supervisor please run::

    $ fab staging supervisor.d


Deploy new version
------------------

Create settings::

    $ cp fabconf.py.def fabconf.py

Set `sudo_user` property of config class.

Add your ssh pub key to projects user::

    $ fab staging push_key

Commit changes to `staging` branch

Deploy::

    $ fab staging deploy


Management supervisor
---------------------

Run supervisorctl::

    $ fab staging supervisor.ctl


Get list of available tasks::

    $ fab -l
