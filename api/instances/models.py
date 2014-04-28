import random

from sqlalchemy.orm import deferred

from api.base.models import BaseModel, db


class Instance(BaseModel, db.Model):
    """ Represents instance, which could be using for exec tasks """
    TYPES_LIST = ['small', 'large']

    name = db.Column(db.String(200), nullable=False, unique=True)
    description = deferred(db.Column(db.Text))
    ip = db.Column(db.String(200), nullable=False)
    type = db.Column(db.Enum(*TYPES_LIST, name='instance_types'),
                     nullable=False)
    is_default = db.Column(db.Boolean, default=False)

    def save(self, commit=True):
        BaseModel.save(self, commit=False)
        if self.is_default:
            Instance.query\
                .filter(Instance.is_default, Instance.name != self.name)\
                .update({Instance.is_default: False})
        if commit:
            db.session.commit()


class Cluster(BaseModel, db.Model):
    STATUS_NEW = 'New'
    STATUS_STARTING = 'Starting'
    STATUS_RUNNING = 'Running'
    STATUS_WAITING = 'Waiting'
    STATUS_ERROR = 'Error'
    STATUS_TERMINATED = 'Terminated'

    PORT_RANGE = (9000, 9010)

    STATUSES = [STATUS_NEW, STATUS_STARTING, STATUS_RUNNING, STATUS_WAITING,
                STATUS_ERROR, STATUS_TERMINATED]

    jobflow_id = db.Column(db.String(200), nullable=False, unique=True)
    master_node_dns = db.Column(db.String(200), nullable=True)
    port = db.Column(db.Integer, nullable=True)
    pid = db.Column(db.Integer, nullable=True)
    status = db.Column(db.Enum(*STATUSES, name='cluster_statuses'),
                       default=STATUS_NEW)
    is_default = db.Column(db.Boolean, default=False)

    def generate_port(self):
        port = None
        exclude = Cluster.query.with_entities(Cluster.port).all()
        while port in exclude or port is None:
            port = random.randrange(*self.PORT_RANGE)
        self.port = port

    @property
    def tunnels(self):
        from api.async_tasks.models import AsyncTask
        return AsyncTask.get_current_by_object(
            self,
            'api.instances.tasks.run_ssh_tunnel',
        )

    @property
    def active_tunnel(self):
        # from api.async_tasks.models import AsyncTask
        # res = AsyncTask.get_current_by_object(
        #     self,
        #     'api.instances.tasks.run_ssh_tunnel',
        #     status='In Progress'
        # )
        # if res:
        #     return res[0]
        return self.pid

    def create_ssh_tunnel(self):
        from api.instances.tasks import run_ssh_tunnel
        run_ssh_tunnel.delay(self.id)
        self.pid = -1  # task delayed
        self.save()

    def terminate_ssh_tunnel(self):
        import os
        import signal
        if self.pid is not None:
            os.kill(self.pid, signal.SIGKILL)
            self.pid = None
            self.save()
            #self.active_tunnel.terminate_task()

    def save(self, commit=True):
        if self.port is None:
            self.generate_port()
        BaseModel.save(self, commit=False)
        if self.is_default:
            Cluster.query\
                .filter(Cluster.is_default, Cluster.name != self.name)\
                .update({Cluster.is_default: False})
        if commit:
            db.session.commit()
