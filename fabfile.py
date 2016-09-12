try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from fabdeploy import monkey
import fabgrunt
monkey.patch_all()

import os
import posixpath
from fabric.api import task, env, settings, local, run, sudo, prefix, cd
from fabric.contrib import files
from fabdeploy.api import *
from fabdeploy.utils import upload_init_template


setup_fabdeploy()


@task
def here(**kwargs):
    fabd.conf.run('here')


@task
def staging(**kwargs):
    fabd.conf.run('staging')


@task
def prod(**kwargs):
    fabd.conf.run('production')

@task
def worker1(**kwargs):
    fabd.conf.run('worker1')

@task
def dev(**kwargs):
    fabd.conf.run('dev')


@task
def install():
    users.create.run()
     #ssh.push_key.run(pub_key_file='~/.ssh/id_rsa.pub')

    fabd.mkdirs.run()

    rabbitmq.install()
    nginx.install.run()

    for app in ['supervisor']:
        pip.install.run(app=app)

    pip.install.run(app='virtualenv', upgrade=True)
    system.package_install.run(packages='liblapack-dev gfortran libpq-dev\
 libevent-dev python-dev mongodb libxml2-dev libxslt-dev libv8-dev scons libboost-python-dev libboost-thread-dev libboost-all-dev')

    # Install nodejs from source
    sudo("wget http://nodejs.org/dist/v0.10.18/node-v0.10.28.tar.gz")
    sudo("tar -zxf node-v0.10.28.tar.gz")
    with cd("node-v0.10.28"):
        sudo("./configure")
        sudo("make")
        sudo("make install")

    # Install NVM
    run("curl https://raw.githubusercontent.com/creationix/nvm/v0.11.1/"
        "install.sh | bash")
    run("source ~/.profile")
    run("nvm install 0.10.28")
    run("nvm alias default 0.10.28")


@task
def push_key():
    ssh.push_key.run(pub_key_file='~/.ssh/id_rsa.pub')


@task
def setup():
    fabd.mkdirs.run()

    release.create.run()
    git.init.run()
    git.push.run()

    #supervisor.push_init_config.run()
    supervisor.push_d_config.run()
    supervisor.push_configs.run()
    supervisor.d.run()

    with settings(warn_only=True):
        rabbitmq.add_user.run()
        rabbitmq.add_vhost.run()
    rabbitmq.set_permissions.run()

    gunicorn.push_nginx_config.run()
    nginx.restart.run()

    virtualenv.create.run()

    # init env for build ui
    #angularjs.init.run()
    fabgrunt.global_npm.run()

    # install numpy and scipy
    with prefix('export LAPACK=/usr/lib/liblapack.so'):
        with prefix('export ATLAS=/usr/lib/libatlas.so'):
            with prefix('export BLAS=/usr/lib/libblas.so'):
                virtualenv.pip_install.run(app='numpy==1.7.1')
                virtualenv.pip_install.run(app='scipy==0.12.0')

    virtualenv.make_relocatable.run()
    release.activate.run()


@task
def qdeploy():
    release.work_on.run(0)
    deploy.run()

@task
def shell():
    release.work_on.run(0)
    flask.shell.run()

@task
def create_db_tables():
    release.work_on.run(0)
    flask.manage.run('create_db_tables')

@task
def migrate():
    release.work_on.run(0)
    flask.manage.run('db upgrade')


@task
def cdeploy():
    release.work_on.run(0)
    git.push.run()
    supervisor.restart_program.run(program='gunicorn')
    supervisor.restart_program.run(program='celeryd')


@task
def deployui():
    release.work_on.run(0)
    git.push.run()
    fabgrunt.private_npm.run()
    fabgrunt.bower.run()
    fabgrunt.activate.run()
    fabgrunt.push_config.run()
    fabgrunt.build.run()
    # angularjs.activate.run()
    # angularjs.push_config.run()
    # angularjs.build.run()


@task
def deploy():
    fabd.mkdirs.run()

    release.create.run()
    git.init.run()
    git.push.run()

    supervisor.push_configs.run()
    flask.push_flask_config.run()
    gunicorn.push_config.run()

    #gunicorn.push_nginx_config.run()
    #nginx.restart.run()

    virtualenv.create.run()
    with prefix('export LAPACK=/usr/lib/liblapack.so'):
        with prefix('export ATLAS=/usr/lib/libatlas.so'):
            with prefix('export BLAS=/usr/lib/libblas.so'):
                virtualenv.pip_install_req.run()
    virtualenv.make_relocatable.run()

    release.activate.run()

    #fabgrunt.private_npm.run()
    #fabgrunt.bower.run()
    #fabgrunt.activate.run()

    fabgrunt.push_config.run()
    fabgrunt.build.run()

    # # angularjs.activate.run()
    # # angularjs.push_config.run()
    # # angularjs.build.run()
    with prefix('export PATH=$PATH:/usr/local/bin'):
        supervisor.update.run()
        supervisor.restart_program.run(program='gunicorn')
        supervisor.restart_program.run(program='celeryd')
        supervisor.restart_program.run(program='celerycam')
    #local('jgit push s3 master:master')


@task
def setupw():
    #supervisor.push_init_config.run()

    fabd.mkdirs.run()
    for app in ['supervisor']:
        pip.install.run(app=app)

    pip.install.run(app='virtualenv', upgrade=True)
    system.package_install.run(packages='liblapack-dev gfortran libpq-dev\
 libevent-dev cloud-utils')
    #upload_init_template('supervisordw.conf')
    #supervisor.push_init_config.run()
    supervisor.push_d_config.run()
    supervisor.push_configs.run()
    supervisor.d.run()
    
    release.create.run()
    virtualenv.create.run()
    # install numpy and scipy
    with prefix('export LAPACK=/usr/lib/liblapack.so'):
        with prefix('export ATLAS=/usr/lib/libatlas.so'):
            with prefix('export BLAS=/usr/lib/libblas.so'):
                virtualenv.pip_install.run(app='numpy')
                virtualenv.pip_install.run(app='scipy')
    virtualenv.make_relocatable.run()
    release.activate.run()


@task
def deployw():
    release.work_on.run(0)
    #upload_init_template(name='supervisordw.conf', name_to='supervisord.conf')
    fabd.mkdirs.run()

    release.create.run()
    git.init.run()
    git.push.run()

    supervisor.push_configs.run()
    flask.push_flask_config.run()

    virtualenv.create.run()
    virtualenv.pip_install_req.run()
    virtualenv.make_relocatable.run()

    release.activate.run()

    supervisor.update.run()
    supervisor.restart_program.run(program='celerydw')


@task
def upload_code_to_s3():
    local('git archive --format=tar master | gzip > cloudml.tar.gz')
    local("s3cmd put cloudml.tar.gz s3://odesk-match-cloudml/cloudml.tar.gz")
