from api.servers.models import Server
from api.ml_models.models import Model
from api.model_tests.models import TestResult
from api.import_handlers.models.importhandlers import XmlImportHandler
from api.servers.models import Server, FOLDER_MODELS, FOLDER_IMPORT_HANDLERS


def update_server_types():
    """
    Sets correct server type (based on name)
    """
    # set production type
    servers = Server.query.filter(Server.name.like('%Production%')).all()
    for server in servers:
        server.type = Server.PRODUCTION
        server.save()
    # set staging type
    servers = Server.query.filter(Server.name.like('%Staging%')).all()
    for server in servers:
        server.type = Server.STAGING
        server.save()


def update_deployed():
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
