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
    FILTER_PARAMS = (('status', str), ('jobflow_id', str))
    Model = Cluster
    ALLOWED_METHODS = ('get', 'put', 'delete', 'options')
    PUT_ACTIONS = ('create_tunnel', 'terminate_tunnel')

    def _set_list_query_opts(self, cursor, params):
        status = params.pop('status', None)
        if status == 'Active':
            cursor = cursor.filter(Cluster.status.in_(Cluster.ACTIVE_STATUSES))
        else:
            cursor = cursor.filter_by(status=status)
        jobflow_id = params.pop('jobflow_id', None)
        if jobflow_id:
            cursor = cursor.filter(Cluster.jobflow_id.ilike('%{0}%'.format(jobflow_id)))
        return cursor

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

    def delete(self, action=None, **kwargs):
        """ Deletes unused model """
        model = self._get_details_query({}, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        # terminating the cluster
        model.terminate_ssh_tunnel()
        model.terminate()
        model.status = Cluster.STATUS_TERMINATED
        model.save()
        return '', 204


api.add_resource(ClusterResource, '/cloudml/instances/clusters/')
