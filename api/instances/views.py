from api import api
from api.base.resources import BaseResourceSQL

from models import Instance, Cluster
from forms import InstanceForm


class InstanceResource(BaseResourceSQL):
    """ Instances API methods """
    Model = Instance
    put_form = post_form = InstanceForm

api.add_resource(InstanceResource, '/cloudml/aws_instances/')


class ClusterResource(BaseResourceSQL):
    """ Cluster API methods """
    Model = Cluster
    ALLOWED_METHODS = ('get', 'put', 'delete', 'options')
    PUT_ACTIONS = ('create_tunnel', 'terminate_tunnel')

    def _put_create_tunnel_action(self, **kwargs):
        cluster = self._get_details_query(None, **kwargs)
        cluster.create_ssh_tunnel()
        data = {'active_tunnel': cluster.active_tunnel}
        return self._render({self.OBJECT_NAME: data})

    def _put_terminate_tunnel_action(self, **kwargs):
        cluster = self._get_details_query(None, **kwargs)
        cluster.terminate_ssh_tunnel()
        data = {'active_tunnel': cluster.active_tunnel}
        return self._render({self.OBJECT_NAME: data})

    def _delete_validataion(self, model):
        """ Terminate cluster """
        model.terminate_ssh_tunnel()
        model.terminate()

api.add_resource(ClusterResource, '/cloudml/instances/clusters/')
