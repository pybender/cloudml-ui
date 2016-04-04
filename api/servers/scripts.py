from api.ml_models.models import Model
from api.model_tests.models import TestResult
from api.import_handlers.models.importhandlers import XmlImportHandler
from api.servers.models import Server, FOLDER_MODELS, FOLDER_IMPORT_HANDLERS
from grafana.grafana import create_server_dashboard


def add_grafana_dashboads():
    """
    Create grafana dashboards for existing models
    """
    servers = Server.query.all()
    for server in servers:
        # update models
        model_files = server.list_keys(FOLDER_MODELS)
        for file_ in model_files:
            model = Model.query.get(file_["object_id"])
            if model:
                create_server_dashboard(server, model)
                print "Model {0} (id#{1}) on server {2} updated".format(
                        model.name,
                        model.id,
                        server.name)

def update_deployed():
    """
    Locks already deployed models and import handlers
    from modifications
    """
    servers = Server.query.all()
    for server in servers:
        # update models
        model_files = server.list_keys(FOLDER_MODELS)
        for file_ in model_files:
            model = Model.query.get(file_["object_id"])
            if model and not model.locked:
                model.locked = True
                model.save()
                model.features_set.locked = True
                model.features_set.save()
                for ds in model.datasets:
                    if not ds.locked:
                        ds.locked = True
                        ds.save()
                model_tests = TestResult.query.filter(
                    TestResult.model_id == model.id).all()
                for test in model_tests:
                    if not test.dataset.locked:
                        ds = test.dataset
                        ds.locked = True
                        ds.save()
                print "Model {0} (id#{1}) updated".format(model.name, model.id)

        # update import handlers
        handler_files = server.list_keys(FOLDER_IMPORT_HANDLERS)
        for file_ in handler_files:
            ih = XmlImportHandler.query.get(file_["object_id"])
            if ih and not ih.locked:
                ih.locked = True
                ih.save()
                print "Import handler {0} (id#{1}) updated".format(ih.name,
                                                                   ih.id)
