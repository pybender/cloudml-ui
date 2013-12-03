from api import api
from api.resources import BaseResourceSQL
from models import *
from forms import *
from api.decorators import public_actions


# # Features specific resources
# class FeatureSetResource(BaseResourceSQL):
#     """
#     Features Set API methods
#     """
#     MESSAGE404 = "Feature set set doesn't exist"
#     OBJECT_NAME = 'set'
#     #post_form = FeatureSetAddForm
#     put_form = FeatureSetForm
#     GET_ACTIONS = ('download', )

#     @property
#     def Model(self):
#         return app.db.FeatureSet

#     @public_actions(['download'])
#     def get(self, *args, **kwargs):
#         return super(FeatureSetResource, self).get(*args, **kwargs)

#     def _get_download_action(self, **kwargs):
#         model = self._get_details_query(None, None, **kwargs)
#         if model is None:
#             raise NotFound(self.MESSAGE404 % kwargs)

#         data = json.dumps(model.to_dict())
#         resp = Response(data)
#         resp.headers['Content-Type'] = 'text/plain'
#         resp.headers['Content-Disposition'] = \
#             'attachment; filename=%s.json' % model.name
#         return resp

# api.add_resource(FeatureSetResource, '/cloudml/features/sets/')


class ClassifierResource(BaseResourceSQL):
    """
    Classifier API methods
    """
    MESSAGE404 = "Classifier doesn't exist"
    OBJECT_NAME = 'classifier'
    post_form = put_form = ClassifierForm
    GET_ACTIONS = ('configuration', )
    Model = PredefinedClassifier

    def _get_configuration_action(self, **kwargs):
        from core.trainer.classifier_settings import CLASSIFIERS
        return self._render({'configuration': CLASSIFIERS})

api.add_resource(ClassifierResource, '/cloudml/features/classifiers/')


class NamedFeatureTypeResource(BaseResourceSQL):
    """
    Tags API methods
    """
    MESSAGE404 = "Named feature type doesn't exist"
    OBJECT_NAME = 'named_type'
    put_form = post_form = NamedFeatureTypeAddForm
    Model = NamedFeatureType

api.add_resource(NamedFeatureTypeResource, '/cloudml/features/named_types/')


class TransformerResource(BaseResourceSQL):
    """
    Transformer API methods
    """
    MESSAGE404 = "transformer doesn't exist"
    OBJECT_NAME = 'transformer'
    put_form = post_form = TransformerForm
    GET_ACTIONS = ('configuration', )
    ALL_FIELDS_IN_POST = True
    Model = PredefinedTransformer

    def _get_configuration_action(self, **kwargs):
        from config import TRANSFORMERS
        return self._render({'configuration': TRANSFORMERS})

api.add_resource(TransformerResource, '/cloudml/features/transformers/')


class ScalersResource(BaseResourceSQL):
    """
    Scalers API methods
    """
    MESSAGE404 = "Scaler doesn't exist"
    OBJECT_NAME = 'scaler'
    put_form = post_form = ScalerForm
    GET_ACTIONS = ('configuration', )
    ALL_FIELDS_IN_POST = True
    Model = PredefinedScaler

    def _get_configuration_action(self, **kwargs):
        from config import SCALERS
        return self._render({'configuration': SCALERS})

api.add_resource(ScalersResource, '/cloudml/features/scalers/')


class FeatureResource(BaseResourceSQL):
    """
    Feature API methods
    """
    MESSAGE404 = "Feature doesn't exist"
    OBJECT_NAME = 'feature'
    put_form = post_form = FeatureForm
    Model = Feature

api.add_resource(
    FeatureResource,
    '/cloudml/features/<regex("[\w\.]*"):feature_set_id>/items/')


class ParamsResource(BaseResourceSQL):
    """
    Parameters API methods
    """
    @property
    def Model(self):
        raise Exception('Invalid operation')

    def get(self, *args, **kwargs):
        from core.trainer.feature_types import FEATURE_TYPE_FACTORIES
        from core.trainer.feature_types import FEATURE_TYPE_DEFAULTS
        from core.trainer.feature_types import FEATURE_PARAMS_TYPES
        _types = [(key, {
            'type': getattr(value, 'python_type', ''),
            'required_params': value.required_params,
            'optional_params': value.optional_params,
            'default_params': value.default_params,
        }) for key, value in FEATURE_TYPE_FACTORIES.items()]
        _conf = {
            'types': dict(_types),
            'params': FEATURE_PARAMS_TYPES,
            'defaults': FEATURE_TYPE_DEFAULTS
        }
        return self._render({'configuration': _conf})

api.add_resource(ParamsResource, '/cloudml/features/params/')
