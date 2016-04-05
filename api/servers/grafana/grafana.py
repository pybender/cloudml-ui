import json
import logging
import os
from slugify import slugify
from grafana_api_client import GrafanaClient, GrafanaClientError
from string import Template
from ..models import Server

from api import app

BASE_PATH = os.path.dirname(__file__)


class GrafanaHelper(object):
    def __init__(self, server):
        self.client = GrafanaClient(
            app.config['GRAFANA_KEY'],
            host=app.config['GRAFANA_HOST'])
        self.server = server

    @property
    def server_name(self):
        if not hasattr(self, '_server_name'):
            self._server_name = self.server.name.replace('_', '-')
        return self._server_name

    def model2grafana(self, model):
        logging.info('Posting %s to server %s Grafana dashboard',
                     model.name, self.server.name)
        dashboard = self._get_or_create_dashboard_json()
        self._model_to_dashboard(dashboard, model)
        self._update_grafana_dashboard(dashboard)
        return dashboard

    def _get_or_create_dashboard_json(self):
        dashboard = self._get_dashboard_json()
        if dashboard is None:
            logging.info('Grafana dashboard for server {0!s} \
not found.'.format(self.server.name))
            dashboard = self._create_dashboard_json()
        return dashboard

    def _get_dashboard_json(self):
        try:
            data = self.client.dashboards.db.__getitem__(
                self.server.grafana_name).get()
            logging.info('Grafana dashboard for server {0!s} \
found.'.format(self.server.name))
            return data['dashboard']
        except GrafanaClientError, exc:
            logging.error('Grafana Error while getting dashboard %s', exc)
        except Exception, exc:
            logging.error('Error while getting dashboard %s', exc)

    def _create_dashboard_json(self, filename='server_tmpl.json'):
        logging.info('Loading server dashboard json from file')
        filename = os.path.join(BASE_PATH, filename)
        with open(filename, 'r') as fp:
            tmpl = fp.read()
        data = Template(tmpl)
        data = data.substitute(name=self.server_name)
        return json.loads(data)

    def _get_model_json(self, model, model_filename='model_tmpl.json'):
        model_filename = os.path.join(BASE_PATH, model_filename)
        with open(model_filename, 'r') as fp:
            model_tmpl = fp.read()

        model_data = Template(model_tmpl)
        model_data = model_data.substitute(
            env=Server.ENV_MAP[self.server.type],
            server=self.server.folder,
            name=model.name)

        return json.loads(model_data)

    def _model_to_dashboard(self, dashboard, model):
        model_json = self._get_model_json(model)
        exist = False
        for index, row in enumerate(dashboard['rows']):
            if row['title'] == model.name:
                dashboard['rows'][index] = model_json
                exist = True
                logging.info('Model found on server {0!s} \
Grafana dashboard.'.format(self.server.name))
                break
        if not exist:
            logging.info('Model not found on server {0!s} \
Grafana dashboard.'.format(self.server.name))
            dashboard['rows'].append(model_json)
        return dashboard

    def _update_grafana_dashboard(self, dashboard):
        logging.info('Updating Grafana dashboard')
        self.client.dashboards.db.create(dashboard=dashboard, overwrite=True)


def create_server_dashboard(server, model):
    helper = GrafanaHelper(server)
    return helper.model2grafana(model)
    # server_name = (server.name).replace('_', '-')
    # server_slug = slugify('Cloudml ' + server_name)
    # try:
    #     data = client.dashboards.db.__getitem__(server_slug).get()
    #     dashboard = data['dashboard']
    # except GrafanaClientError, e:
    #     dashboard = None
    # if not dashboard:
    #     filename = os.path.join(BASE_PATH, filename)
    #     with open(filename, 'r') as fp:
    #         tmpl = fp.read()
    #     data = Template(tmpl)
    #     data = data.substitute(name=server_name)
    #     dashboard = json.loads(data)
    # model_filename = 'model_tmpl.json'
    # model_filename = os.path.join(BASE_PATH, model_filename)
    # with open(model_filename, 'r') as fp:
    #     model_tmpl = fp.read()

    # model_data = Template(model_tmpl)
    # model_data = model_data.substitute(
    #     env=Server.ENV_MAP[server.type],
    #     server=server.folder,
    #     name=model.name)

    # model_json = json.loads(model_data)
    # exist = False
    # for index, row in enumerate(dashboard['rows']):
    #     if row['title'] == model.name:
    #         dashboard['rows'][index] = model_json
    #         exist = True
    #         break
    # if not exist:
    #     dashboard['rows'].append(model_json)
    # client.dashboards.db.create(dashboard=dashboard, overwrite=True)
