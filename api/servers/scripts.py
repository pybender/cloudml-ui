from api.ml_models.models import Model
from api.model_tests.models import TestResult
from api.import_handlers.models.importhandlers import XmlImportHandler
from api.servers.models import Server, FOLDER_MODELS, FOLDER_IMPORT_HANDLERS
from grafana import update_grafana_dashboard


def add_grafana_dashboads():
    """
    Create grafana dashboards for existing models
    """
    servers = Server.query.filter(Server.id.in_((11, 12, 13, 14, 15))).all()
    for server in servers:
        # update models
        model_files = server.list_keys(FOLDER_MODELS)
        for file_ in model_files:
            model = Model.query.get(file_["object_id"])
            if model:
                update_grafana_dashboard(server, model)
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
                    if test.dataset and not test.dataset.locked:
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


def set_server_ids():
    """Sets servers ids where object is deployed"""
    servers = Server.query.all()
    models = {}
    ihs = {}
    for server in servers:
        print "Process server #{0} {1}".format(server.id, server.name)
        for key in server.list_keys(folder=FOLDER_MODELS):
            k = str(key['object_id'])
            if k in models and not server.id in models[k]:
                models[k].append(server.id)
            else:
                models[k] = [server.id]

        for key in server.list_keys(folder=FOLDER_IMPORT_HANDLERS):
            k = str(key['object_id'])
            if k in ihs and not server.id in ihs[k]:
                ihs[k].append(server.id)
            else:
                ihs[k] = [server.id]

    for model, ids in models.iteritems():
        print "Update model #{0} with {1}".format(model, ids)
        m = Model.query.get(int(model))
        if m:
            m.servers_ids = ids
            m.save()

    for model, ids in ihs.iteritems():
        print "Update import handler #{0} with {1}".format(model, ids)
        m = XmlImportHandler.query.get(int(model))
        if m:
            m.servers_ids = ids
            m.save()