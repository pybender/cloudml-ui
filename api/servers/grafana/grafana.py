import json
import os
from slugify import slugify
from grafana_api_client import GrafanaClient, GrafanaClientError
from string import Template

from api import app

BASE_PATH = os.path.dirname(__file__)


client = GrafanaClient(
    app.config['GRAFANA_KEY'],
    host=app.config['GRAFANA_HOST'])


def create_server_dashboard(server, model, filename='server_tmpl.json'):
    server_name = (server.name).replace('_', '-')
    server_slug = slugify('Cloudml ' + server_name)
    try:
        data = client.dashboards.db.__getitem__(server_slug).get()
        dashboard = data['dashboard']
    except GrafanaClientError, e:
        dashboard = None
    if not dashboard:
        filename = os.path.join(BASE_PATH, filename)
        with open(filename, 'r') as fp:
            tmpl = fp.read()
        data = Template(tmpl)
        data = data.substitute(name=server_name)
        dashboard = json.loads(data)
    model_filename = 'model_tmpl.json'
    model_filename = os.path.join(BASE_PATH, model_filename)
    with open(model_filename, 'r') as fp:
        model_tmpl = fp.read()

    env_map = {'Production': 'prod',
                   'Staging': 'staging',
                   'Development': 'dev'}
    model_data = Template(model_tmpl)
    model_data = model_data.substitute(
        env=env_map[server.type],
        server=server.folder,
        name=model.name
        )


    model_json = json.loads(model_data)
    exist = False
    for index, row in enumerate(dashboard['rows']):
        if row['title'] == model.name:
            dashboard['rows'][index] = model_json
            exist = True
            break
    if not exist:
        dashboard['rows'].append(model_json)    
    client.dashboards.db.create(dashboard=dashboard, overwrite=True)
