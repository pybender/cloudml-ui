from core.trainer.scalers import MinMaxScaler, StandardScaler


# TODO: move and use it in cloudml project
TRANSFORMERS = {
    'Dictionary': {
        #'mthd': get_dict_vectorizer,
        'parameters': ['separator', 'sparse'],
        'default': {},  # default value
        'defaults': {}  # default values of the parameters
    },
    'Count': {
        #'mthd': get_count_vectorizer,
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
        #'mthd': get_tfidf_vectorizer,
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
        #'mthd': get_count_vectorizer,
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
        #'mthd': get_count_vectorizer,
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
    }
}


SCALERS = {
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

#INV_FIELDS_MAP = {v:k for k, v in FIELDS_MAP.items()}


from core.trainer.classifier_settings import *
CLASSIFIERS = {
    LOGISTIC_REGRESSION: {
        'cls': 'sklearn.linear_model.LogisticRegression',
        'parameters': [
            {'name': "penalty",
             'type': 'string',
             'choices': ['l1', 'l2'],
             'default': 'l2',
             'required': True},
            {'name': "C", 'type': 'float'},
            {'name': "dual", 'type': 'boolean'},
            {'name': "fit_intercept", 'type': 'boolean'},
            {'name': "intercept_scaling", 'type': 'float'},
            {'name': "class_weight", 'type': 'auto_dict'},
            {'name': "tol", 'type': 'float'}],
        'defaults': {'penalty': 'l2'}
       },
       SGD_CLASSIFIER: {
           'cls': 'sklearn.linear_model.SGDClassifier',
           'parameters': (
              {'name': 'loss',
               'type': 'string',
               'choices': ['hinge', 'log', 'modified_huber', 'squared_hinge',
                           'perceptron', 'squared_loss', 'huber',
                           'epsilon_insensitive', 'squared_epsilon_insensitive']},
              {'name': 'penalty',
               'type': 'string',
               'choices': ['l1', 'l2', 'elasticnet'],},
              {'name': 'alpha', 'type': 'float'},
              {'name': 'l1_ratio', 'type': 'float'},
              {'name': 'fit_intercept', 'type': 'boolean'},
              {'name': 'n_iter', 'type': 'integer'},
              {'name': 'shuffle', 'type': 'boolean'},
              {'name': 'verbose', 'type': 'integer'},
              {'name': 'epsilon', 'type': 'float'},
              {'name': 'n_jobs', 'type': 'integer'},
              {'name': 'random_state', 'type': 'integer'},
              {'name': 'learning_rate', 'type': 'string'},
              {'name': 'eta0', 'type': 'float'},
              {'name': 'power_t', 'type': 'float'},
              {'name': 'class_weight', 'type': 'dict'},
              {'name': 'warm_start', 'type': 'boolean'},
              {'name': 'rho', 'type': 'string'},
              {'name': 'seed', 'type': 'string'}),
           'defaults': {'n_iter': 20, 'shuffle': True}
       },
       SVR: {
           'cls': 'sklearn.svm.SVR',
           'parameters': (
              {'name': "C", 'type': 'float'},
              {'name': 'epsilon', 'type': 'float'},
              {'name': 'kernel', 'type': 'string'},
              {'name': 'degree', 'type': 'integer'},
              {'name': 'gamma', 'type': 'float'},
              {'name': 'coef0', 'type': 'float'},
              {'name': 'probability', 'type': 'boolean'},
              {'name': 'shrinking', 'type': 'boolean'}
            ),
           'defaults': {'C': 1.0, 'epsilon': 0.1}
          }
       }
