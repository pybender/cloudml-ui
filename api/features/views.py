""" Features specific resources """

# Authors: Nikolay Melnik <nmelnik@upwork.com>

from api import api
from api.base.resources import BaseResourceSQL, public_actions, NotFound
from api.base.resources.utils import odesk_error_response
from models import *
from forms import *
from config import CLASSIFIERS
from api.base.exceptions import InvalidOperationError


class FeatureSetResource(BaseResourceSQL):
    """
    Features Set API methods
    """
    MESSAGE404 = "Feature set set doesn't exist"
    OBJECT_NAME = 'set'
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
        return self._render({'configuration': CLASSIFIERS})

    def post(self, **kwargs):
        form = self.post_form(Model=self.Model, **kwargs)
        if form.is_valid() and 'model_id' in form.cleaned_data:
            model = Model.query.get(form.cleaned_data['model_id'])
            if not api.app.config['MODIFY_DEPLOYED_MODEL'] and \
               model is not None and model.locked:
                return odesk_error_response(
                    405, 405, 'Model is deployed and blocked for '
                    'modifications. Forbidden to change it\'s classifier.')
        return super(ClassifierResource, self).post(**kwargs)

api.add_resource(ClassifierResource, '/cloudml/features/classifiers/')


class NamedTypeResource(BaseResourceSQL):
    """ Predefined named feature types API methods """
    put_form = post_form = NamedFeatureTypeForm
    Model = NamedFeatureType

api.add_resource(NamedTypeResource, '/cloudml/features/named_types/')


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
        raise InvalidOperationError('Invalid operation')

    def get(self, *args, **kwargs):
        from cloudml.trainer.feature_types import FEATURE_TYPE_FACTORIES
        from cloudml.trainer.feature_types import FEATURE_TYPE_DEFAULTS
        from cloudml.trainer.feature_types import FEATURE_PARAMS_TYPES
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
