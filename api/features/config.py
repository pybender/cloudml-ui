from core.trainer.scalers import MinMaxScaler, StandardScaler, NoScaler


# TODO: move and use it in cloudml project
TRANSFORMERS = {
    'Dictionary': {
        'parameters': ['separator', 'sparse'],
        'default': {},  # default value
        'defaults': {}  # default values of the parameters
    },
    'Count': {
        'parameters': ['charset', 'charset_error',
                       'strip_accents', 'lowercase',
                       'stop_words', 'token_pattern',
                       'analyzer', 'max_df', 'min_df',
                       'max_features', 'vocabulary',
                       'ngram_range_min',
                       'ngram_range_max',
                       'binary'],
        'default': '',
        'defaults': {}
    },
    'Tfidf': {
        'parameters': ['charset', 'charset_error',
                       'strip_accents', 'lowercase',
                       'analyzer', 'stop_words',
                       'token_pattern', 'max_df',
                       'min_df', 'max_features',
                       'vocabulary', 'binary',
                       'use_idf', 'smooth_idf',
                       'ngram_range_min',
                       'ngram_range_max',
                       'sublinear_tf'],
        'default': '',
        'defaults': {}
    },
    'Lda': {
        'parameters': ['charset', 'charset_error',
                       'strip_accents', 'lowercase',
                       'stop_words', 'token_pattern',
                       'analyzer', 'max_df', 'min_df',
                       'max_features', 'vocabulary',
                       'binary',
                       'num_topics', 'id2word', 'alpha',
                       'eta', 'distributed', 'topic_file'],
        'default': '',
        'defaults': {}
    },
    'Lsi': {
        'parameters': ['charset', 'charset_error',
                       'strip_accents', 'lowercase',
                       'stop_words', 'token_pattern',
                       'analyzer', 'max_df', 'min_df',
                       'max_features', 'vocabulary',
                       'binary',
                       'num_topics', 'id2word',
                       'distributed', 'onepass',
                       'power_iters', 'extra_samples',
                       'topic_file'],
        'default': '',
        'defaults': {}
    },
    'Ntile': {
        'parameters': ['number_tile'],
        'default': '',
        'defaults': {}
    }
}


SCALERS = {
    'NoScaler': {
        'class': NoScaler,
        'defaults': {},
        'parameters': []},
    'MinMaxScaler': {
        'class': MinMaxScaler,
        'defaults': {
            'feature_range_min': 0,
            'feature_range_max': 1,
            'copy': True},
        'parameters': ['feature_range_min', 'feature_range_max', 'copy']},
    'StandardScaler': {
        'class': StandardScaler,
        'defaults': {
            'copy': True,
            'with_std': True,
            'with_mean': True},
        'parameters': ['copy', 'with_std', 'with_mean']
    }
}

SYSTEM_FIELDS = ('name', 'created_on', 'updated_on', 'created_by',
                 'updated_by', 'type', 'is_predefined', 'feature_set')

FIELDS_MAP = {'input_format': 'input-format',
              'is_target_variable': 'is-target-variable',
              'required': 'is-required',
              'schema_name': 'schema-name'}

from core.trainer.classifier_settings import CLASSIFIERS
