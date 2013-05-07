try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

from fabdeploy import monkey
monkey.patch_all()
import os
import posixpath
from fabric.api import task, env, settings, local, run, sudo, prefix
from fabric.contrib import files
from fabdeploy.api import *


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
def dev(**kwargs):
    fabd.conf.run('dev')


@task
def test(**kwargs):
    fabd.conf.run('test')


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
npm nodejs')


@task
def push_key():
    ssh.push_key.run(pub_key_file='~/.ssh/id_rsa.pub')


@task
def setup():
    fabd.mkdirs.run()

    supervisor.push_init_config.run()
    supervisor.push_d_config.run()
    supervisor.push_configs.run()
    supervisor.d.run()

    with settings(warn_only=True):
        rabbitmq.add_user.run()
        rabbitmq.add_vhost.run()
    rabbitmq.set_permissions.run()

    gunicorn.push_nginx_config.run()
    nginx.restart.run()

    # init env for build ui
    run('cd %(project_path)s/ui; ./scripts/init.sh' % env.conf)



@task
def qdeploy():
    release.work_on.run(0)
    deploy.run()


@task
def deploy():
    fabd.mkdirs.run()

    release.create.run()
    git.init.run()
    git.push.run()

    supervisor.push_configs.run()
    flask.push_flask_config.run()
    gunicorn.push_config.run()

    virtualenv.create.run()
    with prefix('export LAPACK=/usr/lib/liblapack.so'):
        with prefix('export ATLAS=/usr/lib/libatlas.so'):
            with prefix('export BLAS=/usr/lib/libblas.so'):
                virtualenv.pip_install.run(app='numpy')
                virtualenv.pip_install.run(app='scipy')
    virtualenv.pip_install_req.run()
    virtualenv.make_relocatable.run()

    run('cd %(project_path)s/ui; ./scripts/production.sh' % env.conf)

    release.activate.run()

    supervisor.update.run()
    supervisor.restart_program.run(program='celeryd')
    supervisor.restart_program.run(program='celerycam')
    supervisor.restart_program.run(program='gunicorn')


class PushAnjularConfig(Task):
    @conf
    def from_file(self):
        return os.path.join(
            self.conf.django_dir, self.conf.remote_anjsettings_lfile)

    @conf
    def to_file(self):
        return posixpath.join(
            self.conf.django_path, self.conf.local_anjsettings_file)

    def do(self):
        files.upload_template(
            self.conf.from_file,
            self.conf.to_file,
            context=self.conf,
            use_jinja=True)

push_anj_config = PushAnjularConfig()
