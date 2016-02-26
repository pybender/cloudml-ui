"""
Instance related models.
"""

# Authors: Nikolay Melnik <nmelnik@upwork.com>

import random
import logging

from sqlalchemy.orm import deferred

from api.base.models import BaseModel, db
from api.amazon_utils import AmazonEMRHelper


class Instance(BaseModel, db.Model):
    """
    Represents instance, which could be using for exec tasks
    """
    TYPES_LIST = ['small', 'large']

    name = db.Column(db.String(200), nullable=False, unique=True)
    description = deferred(db.Column(db.Text))
    ip = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(*TYPES_LIST, name='instance_types'),
                     nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    def save(self, commit=True):
        super(Instance, self).save(False)
        if self.is_default:
            Instance.query\
                .filter(Instance.is_default, Instance.name != self.name)\
                .update({Instance.is_default: False})
        if commit:
            db.session.commit()

    def __repr__(self):
        return "<Instance %s>" % self.name


class Cluster(BaseModel, db.Model):
    STATUS_NEW = 'New'
    STATUS_STARTING = 'Starting'
    STATUS_RUNNING = 'Running'
    STATUS_WAITING = 'Waiting'
    STATUS_ERROR = 'Error'
    STATUS_TERMINATED = 'Terminated'

    PENDING = -1

    PORT_RANGE = (9000, 9010)

    STATUSES = [STATUS_NEW, STATUS_STARTING, STATUS_RUNNING, STATUS_WAITING,
                STATUS_ERROR, STATUS_TERMINATED]
    ACTIVE_STATUSES = [STATUS_NEW, STATUS_STARTING, STATUS_RUNNING,
                       STATUS_WAITING, STATUS_ERROR]

    jobflow_id = db.Column(db.String(200), nullable=False, unique=True)
    master_node_dns = db.Column(db.String(200), nullable=True)
    port = db.Column(db.Integer, nullable=True)
    pid = db.Column(db.Integer, nullable=True)
    status = db.Column(db.Enum(*STATUSES, name='cluster_statuses'),
                       default=STATUS_NEW)
    logs_folder = db.Column(db.String(200), nullable=True)

    # FIXME: do we need this field?
    is_default = db.Column(db.Boolean, default=False)

    def generate_port(self):
        """
        Generates random port which isn't used by any other cluster.

        Available ports are in range: `PORT_RANGE`.
        """
        exclude = set([cl[0] for cl in Cluster.query.with_entities(
            Cluster.port).filter(Cluster.status!=Cluster.STATUS_TERMINATED, Cluster.status!=Cluster.STATUS_ERROR)])
        ports = list(set(xrange(*self.PORT_RANGE)) - exclude)
        if ports:
            self.port = random.choice(ports)
        else:
            raise ValueError('All ports are busy')

    @property
    def tunnels(self):
        from api.async_tasks.models import AsyncTask
        return AsyncTask.get_current_by_object(
            self,
            'api.instances.tasks.run_ssh_tunnel',
        )

    @property
    def active_tunnel(self):
        return self.pid

    def create_ssh_tunnel(self):
        from api.instances.tasks import run_ssh_tunnel
        if self.pid is None:
            # task delayed
            self.pid = self.PENDING
            self.save()
            run_ssh_tunnel.delay(self.id)

    def terminate_ssh_tunnel(self):
        import os
        import signal
        if self.pid is not None and self is not self.PENDING:
            try:
                os.kill(self.pid, signal.SIGKILL)
            except Exception, exc:
                logging.error("Unknown error occures, while removing "
                              "process: {0}".format(exc))
            self.pid = None
            self.save()

    def terminate(self):
        emr = AmazonEMRHelper()
        emr.terminate_jobflow(self.jobflow_id)

    def save(self, commit=True):
        if self.port is None:
            self.generate_port()
        super(Cluster, self).save(commit)
