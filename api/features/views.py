""" Features specific resources """
from api import api
from api.base.resources import BaseResourceSQL, public_actions, odesk_error_response, ERR_INVALID_DATA

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
    POST_ACTIONS = ('copy_from_trainer', )
    ALL_FIELDS_IN_POST = True
    Model = PredefinedTransformer

    def _get_configuration_action(self, **kwargs):
        from config import TRANSFORMERS
        return self._render({'configuration': TRANSFORMERS})

    def _post_copy_from_trainer_action(self, **kwargs):
        def encode_vocabulary(obj):
            import numpy
            if isinstance(obj, numpy.int32):
                return int(obj)
            else:
                return obj

        form = CopyTransformerForm(Model=PredefinedTransformer)
        if form.is_valid():
            model = form.cleaned_data['model']
            feature = form.cleaned_data['feature']
            name = form.cleaned_data['name']

            if not feature.transformer:
                return odesk_error_response(
                    400, ERR_INVALID_DATA,
                    'Feature does not have any transformer')

            if model.features_set_id != feature.feature_set_id:
                return odesk_error_response(400, ERR_INVALID_DATA,
                                            'Feature of other model')

            trainer = model.get_trainer()
            if feature.name not in trainer._feature_model.features:
                return odesk_error_response(400, ERR_INVALID_DATA,
                                            'Wrong feature name')

            trainer_feature = trainer._feature_model.features[feature.name]
            transformer = trainer_feature.get('transformer', None)
            vocab = transformer.vocabulary_ if transformer else None

            vocab = json.dumps(vocab, default=encode_vocabulary)

            new_transformer = PredefinedTransformer()
            new_transformer.vocabulary = vocab
            new_transformer.vocabulary_size = len(vocab)
            new_transformer.name = name
            new_transformer.type = feature.transformer['type']
            new_transformer.params = feature.transformer['params']
            new_transformer.save()

            return self._render(
                {'transformer': self._prepare_model(new_transformer, kwargs)},
                code=201)

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
    FILTER_PARAMS = (('transformer', str), )

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
