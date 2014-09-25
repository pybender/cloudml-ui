__author__ = 'nader'

import os
import posixpath

from fabric.api import run
from fabric.contrib import files

from fabdeploy.containers import conf
from fabric.operations import sudo
from fabdeploy.task import Task


__all__ = [
    'global_npm',
    'private_npm'
    'bower',
    'activate',
    'push_config',
    'build',
    'init'
]


class GlobalNPM(Task):

    def do(self):
        sudo('npm cache clean')
        sudo('npm install -g grunt-cli bower coffee-script')

global_npm = GlobalNPM()


class PrivateNPM(Task):
    @conf
    def options(self):
        return ''

    def do(self):
        run('npm cache clean')
        run('rm -r --force %(project_path)s/ui/node_modules' % self.conf)
        run('cd %(project_path)s/ui; npm install --production' % self.conf)
        run('cp -r %(project_path)s/ui/node_modules %(var_path)s/node_modules' % self.conf)
        run('rm -r --force %(project_path)s/ui/node_modules' % self.conf)

private_npm = PrivateNPM()


class Bower(Task):
    @conf
    def options(self):
        return ''

    def do(self):
        run('bower cache clean')
        run('rm -r --force %(project_path)s/ui/bower_components' % self.conf)
        run('cd %(project_path)s/ui; bower install --production' % self.conf)
        run('cp -r %(project_path)s/ui/bower_components %(var_path)s/bower_components' % self.conf)
        run('rm -r --force %(project_path)s/ui/bower_components' % self.conf)

bower = Bower()


class Activate(Task):
    @conf
    def options(self):
        return ''

    def do(self):
        run('ln '
            '--symbolic '
            '--force '
            '--no-target-directory '
            '%(var_path)s/bower_components %(project_path)s/ui/bower_components' % self.conf)

        run('ln '
            '--symbolic '
            '--force '
            '--no-target-directory '
            '%(var_path)s/bower_components %(project_path)s/ui/bower_components' % self.conf)

activate = Activate()


class PushConfig(Task):
    @conf
    def from_file(self):
        return os.path.join(
            self.conf.project_dir, self.conf.remote_anjsettings_lfile)

    @conf
    def to_file(self):
        return posixpath.join(
            self.conf.project_path, self.conf.local_anjsettings_file)

    def do(self):
        files.upload_template(
            self.conf.from_file,
            self.conf.to_file,
            context=self.conf,
            use_jinja=True)

push_config = PushConfig()


class Build(Task):
    @conf
    def options(self):
        return ''

    def do(self):
        run('cd %(project_path)s/ui; grunt build:production' % self.conf)

build = Build()
#
#
# class Init(Task):
#     @conf
#     def options(self):
#         return ''
#
#     def do(self):
#         run('cd %(project_path)s/ui; ./scripts/init.sh' % self.conf)
#         run('cp -r %(project_path)s/ui/node_modules %(var_path)s/node_modules' % self.conf)
#         run('rm -r --force %(project_path)s/ui/node_modules' % self.conf)
#
# init = Init()
