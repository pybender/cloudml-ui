""" Features specific resources """
from api import api
from api.base.resources import BaseResourceSQL
from api.decorators import public_actions

from models import *
from forms import *


class FeatureSetResource(BaseResourceSQL):
    """
    Features Set API methods
    """
    MESSAGE404 = "Feature set set doesn't exist"
    OBJECT_NAME = 'set'
    #post_form = FeatureSetAddForm
    put_form = FeatureSetForm
    GET_ACTIONS = ('download', )
    Model = FeatureSet

    @public_actions(['download'])
    def get(self, *args, **kwargs):
        return super(FeatureSetResource, self).get(*args, **kwargs)

    def _get_download_action(self, **kwargs):
        model = self._get_details_query(None, None, **kwargs)
        if model is None:
            raise NotFound(self.MESSAGE404 % kwargs)

        data = json.dumps(model.to_dict())
        resp = Response(data)
        resp.headers['Content-Type'] = 'text/plain'
        resp.headers['Content-Disposition'] = \
            'attachment; filename=%s.json' % model.name
        return resp

api.add_resource(FeatureSetResource, '/cloudml/features/sets/')


class ClassifierResource(BaseResourceSQL):
    """ Classifier API methods """
    post_form = put_form = ClassifierForm
    GET_ACTIONS = ('configuration', )
    Model = PredefinedClassifier

    def _get_configuration_action(self, **kwargs):
        from core.trainer.classifier_settings import CLASSIFIERS
        return self._render({'configuration': CLASSIFIERS})

api.add_resource(ClassifierResource, '/cloudml/features/classifiers/')


class NamedTypeResource(BaseResourceSQL):
    """ Predefined named feature types API methods """
    put_form = post_form = NamedFeatureTypeAddForm
    Model = NamedFeatureType

api.add_resource(NamedTypeResource, '/cloudml/features/named_types/')


class TransformerResource(BaseResourceSQL):
    """ Transformer API methods """
    put_form = post_form = TransformerForm
    GET_ACTIONS = ('configuration', )
    ALL_FIELDS_IN_POST = True
    Model = PredefinedTransformer

    def _get_configuration_action(self, **kwargs):
        from config import TRANSFORMERS
        return self._render({'configuration': TRANSFORMERS})

api.add_resource(TransformerResource, '/cloudml/features/transformers/')


class ScalerResource(BaseResourceSQL):
    """ Scalers API methods """
    put_form = post_form = ScalerForm
    GET_ACTIONS = ('configuration', )
    ALL_FIELDS_IN_POST = True
    Model = PredefinedScaler

    def _get_configuration_action(self, **kwargs):
        from config import SCALERS
        return self._render({'configuration': SCALERS})

api.add_resource(ScalerResource, '/cloudml/features/scalers/')


class FeatureResource(BaseResourceSQL):
    """ Feature API methods """
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
