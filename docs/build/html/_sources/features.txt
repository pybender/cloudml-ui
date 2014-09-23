.. _features:

========================
Feature JSON file format
========================

It includes information like:

1. The classifier's configuration.
2. The features (and their name).
3. The type of each feature. This might imply transformation to be done on each item of data.
4. Generic feature types, in case more than one feature share the same feature type.
5. Transformers and scalers, that allow converting features to different formats (i.e. Tfidf for converting a text feature to a matrix of TF-IDF features).

.. seealso::

	If you migrating your old import handler files just take a look to
	:ref:`changes in json files <json_changes>`

Here's an example of such a file::


    {
	  "schema-name": "bestmatch",
	  "classifier": {
	    "type": "logistic regression",
	    "params": {"penalty": "l2"}
	  },
	  "feature-types":[
	    {
	      "name":"str_to_timezone",
	      "type": "composite",
	      "params": {
	        "chain": [
	          { "type": "regex", "params": { "pattern": "UTC([-\\+]+\\d\\d).*"  }},
	          { "type": "int" }
	        ]
	      }
	    }
	  ],
	  "features":[
	    {
	      "name":"hire_outcome",
	      "type":"map",
	      "params": {
	        "mappings":{
	          "class1": 1,
	          "class2": 0
	        }
	      },
	      "is-target-variable":true
	    },
	    {
	      "name":"tsexams",
	      "type": "float",
	      "input-format": "dict",
	      "default": 0.33,
	      "is-required": false
	    },
	    {
	      "name":"contractor.dev_blurb",
	      "type": "text",
	      "transformer":{
	        "type":"Tfidf",
	        "params": {"ngram_range_min":1,
	                  "ngram_range_max":1,
	                  "min_df":10}
	      }
	    },
	    {
	      "name":"contractor.dev_timezone",
	      "type":"str_to_timezone"
	    }
	  ]
	}



There are four top-level elements:

* :ref:`classifier <classifier>` - defining the configuration of the classifier to use
* `schema-name` - a string describing the schema in the document
* :ref:`feature-types <named_feature_types>` - a list of feature type definitions
* :ref:`features <features_list>` - a list of the features that the trainer will read from the data

.. _classifier:

Classifier
==========

The first section of features.json is used to define the configuration of the classifier to use. The available options are the following:

====================    ========   ===========
Name                    Required   Description
====================    ========   ===========
name                    yes        The name of the resulting feature
type                    yes        Classifier type
params                  no         Parameters for each type of classifier would be different.
====================    ========   ===========

Currently following types of classifiers could be used:

* :ref:`logistic regression <classifier-logistic-regression>`
* :ref:`support vector regression <classifier-support-vector-regression>`
* :ref:`stochastic gradient descent classifier <classifier-stochastic-gradient-descent-classifier>`


.. _classifier-logistic-regression:

Logistic Regression
-------------------

`Scikit Learn LogisticRegression <http://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html#sklearn.linear_model.LogisticRegression>`_ will be used as the underlying implementation.


This classifier has following parameters:

=================     ============   =============   ===============
Name                  Type           Default         Description
=================     ============   =============   ===============
penalty               string:        'l2'            Specifies the norm used in the penalization
                      'l1','l2'   
dual                  boolean                        Dual or primal formulation. Dual formulation is only implemented for l2 penalty. Prefer dual=False when n_samples > n_features.
C                     float                          Specifies the strength of the regularization. The smaller it is the bigger is the regularization
fit_intercept         boolean                        Specifies if a constant (a.k.a. bias or intercept) should be added the decision function.
intercept_scaling     float                          when self.fit_intercept is True, instance vector x becomes [x, self.intercept_scaling], i.e. a “synthetic” feature with constant value equals to intercept_scaling is appended to the instance vector. The intercept becomes intercept_scaling * synthetic feature weight Note! the synthetic feature weight is subject to l1/l2 regularization as all other features. To lessen the effect of regularization on synthetic feature weight (and therefore on the intercept) intercept_scaling has to be increased
class_weight          dict                           Over-/undersamples the samples of each class according to the given weights. If not given, all classes are supposed to have weight one. The ‘auto’ mode selects weights inversely proportional to class frequencies in the training set.
tol                   float                          Tolerance for stopping criteria.
=================     ============   =============   ===============


.. _classifier-support-vector-regression:

Support Vector Regression
-------------------------

`Scikit Learn SGDClassifier <http://scikit-learn.org/stable/modules/generated/sklearn.linear_model.SGDClassifier.html#sklearn-linear-model-sgdclassifier>`_ will be used as the underlying implementation.

=================     ============   =============   ===============
Name                  Type           Default         Description
=================     ============   =============   ===============
loss
penalty
alpha
l1_ratio
fit_intercept
n_iter                               20
shuffle                              True
verbose
epsilon
n_jobs
random_state
learning_rate
eta0
power_t
class_weight
warm_start
rho
seed
=================     ============   =============   ===============

.. _classifier-stochastic-gradient-descent-classifier:

Stochastic Gradient Descent Classifier
--------------------------------------

`Scikit Learn SVR <http://scikit-learn.org/stable/modules/generated/sklearn.svm.SVR.html#sklearn-svm-svr>`_ will be used as the underlying implementation.

=================     ============   =============   ===============
Name                  Type           Default         Description
=================     ============   =============   ===============
C
epsilon
kernel
degree
gamma
coef0
probability
shrinking
=================     ============   =============   ===============

.. _named_feature_types:

Named feature types
===================

This is user-specific feature types.

Feature type definitions is a list of JSON objects. Each JSON object might
have the following keys and values:

================= =============== ====================
Name              Required        Description
================= =============== ====================
name              yes             The name of the feature type. Will be used later in the document by features so that they can reference the appropriate feature type.
type              yes             :ref:`feature type <core_feature_types>`
params            no              A map of parameters that might be required by the type.
================= =============== ====================

.. note::
    
    You could add feature types to be used system wide in the `Predefined feature types page <http://cloudml.int.odesk.com/#/predefined/types>`_.


.. _features_list:

Features
========

Features are the actual source for the trainer. A feature plan may contain at
least one feature. The definition of each feature might include the following
keys and values

=================== =============== ====================
Name                Required        Description
=================== =============== ====================
name                yes             name of the feature
type                yes             one of :ref:`feature type <core_feature_types>` or named feature type
params              no              A map of parameters that might be required by the type
is-target-variable  no              Can be either true or false. Default value is false. If set to true, then this feature is considered the target variable (or class) for the data
transformer         no              Defines a transformer to use for applying to the data of this feature in order to produce multiple features. See :ref:`transformers <feature_transformers>` for more details.
scaler              no              See :ref:`scalers <feature_scalers>` for more details.
is-required         no              Defines whether this is a required feature or not.Default is true. When processing input data, a check is performed on each input "row" to see if input data for this feature are empty. Data that are null or have length equal to zero (strings, lists, dictionaries, tuples) are considered as empty.
default             no              Defines a default value to use if value read is null or empty        
=================== =============== ====================

.. note::
	.. raw:: html

	    Data that are null or have length equal to zero (strings, lists, dictionaries, tuples) are considered as empty. In this case, the trainer will try to find a default value using the following priority:
	    <ol>
	      <li>If a default value has been defined on the feature model, it will be used</li>
	      <li>If a transformer is defined, then the following values will be used as defaults:
	        <ul>
	          <li>Dictionary - empty dictionary - {}</li>
	          <li>Count - empty string - ''</li>
	          <li>Tfidf - empty string - ''</li>
	          <li>Scale - 0.0</li>
	        </ul>
	      </li>
	      <li>Finally, if a type is defined, then the following defaults will be used:
	          <ul>
	            <li>int - 0</li>
	            <li>float - 0.0</li>
	            <li>boolean - false</li>
	            <li>date - 946684800 (January 1st, 2000)</li>
	          </ul>
	      </li>
	    </ol>


.. _core_feature_types:

Feature types defined in CloudML core
-------------------------------------


================= ==================== =================
Name              Parameters           Description
================= ==================== =================
int                                    Converts each item to an integer. In case the value is null, the trainer checks for parameter named default. If it is set, then its value is used, otherwise 0 is used.
float                                  Converts each item to a integer. In case the value is null, the trainer checks for parameter named default. If it is set, then its value is used, otherwise 0.0 is used.
boolean                                Converts number to boolean. Uses python bool() function. Thus bool(0) = false, bool(null) = false, bool('') = false.
numeric
date              pattern              Parses the input value as a date using the pattern defined in parameter 'pattern'. The result is converted to UNIX timestamp.
regex             pattern              Uses the regular expression defined in parameter pattern to transform the input string. Note that in case of multiple matches, only the first one is used
map               pattern              Looks up the input value in the directory defined by parameter 'mappings'. If there is no key in the directory equal to the input value, null is returned.
composite         chain                Allows applying multiple types to input data. Parameter chain defines a list of types, which are applied sequentially to the input value. For example, first type can be a regular expression, while second a mapping.
categorical_label
categorical
text
================= ==================== =================

.. _feature_scalers:

Feature Scalers
---------------

Scalers allow standardize features by removing the mean and scaling to unit variance. The following table contains a list of available scalers


+----------------+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Name           | Parameters                                 | Description                                                                                                                                                |
+================+============================================+============================================================================================================================================================+
| StandartScaler | feature_range_min, feature_range_max, copy | underlying implementation is `scikit-learn's StandartScaler <http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html>`_ |
+----------------+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+
| MinMaxScaler   | copy, with_std, with_mean                  | underlying implementation is `scikit-learn's MinMaxScaler <http://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.MinMaxScaler.html>`_     |
+----------------+--------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------+


.. note::
    
    You could add feature scalers to be used system wide in the `Predefined feature scalers page <http://cloudml.int.odesk.com/#/predefined/scalers>`_.

.. _feature_transformers:

Feature Transformers
--------------------

Transformers allow creating multiple features from a single one. Each feature might have only one transformer. You can define a transformer by specifying key "name" and any of the appropriate parameters for the transformer. The following table contains a list of available transformers

+------------+-------------------------+----------------------------------------------+ 
| Name       | Parameters              | Description                                  | 
+============+=========================+==============================================+ 
| Dictionary | separator               | Transforms lists of key-value                |
|            | sparse                  |  charset  charset_error                      | 
+------------+-------------------------+----------------------------------------------+ 
| Count      | charset  charset_error  | Converts text documents to a collection      |
|            | strip_accents lowercase | of string tokens and their counts            |
|            | stop_words token_pattern|                                              |
|            | analyzer  max_df  min_df|                                              |
|            | max_features vocabulary |                                              |
|            | binary, ngram_range_min |                                              |
|            | ngram_range_max         |                                              |
+------------+-------------------------+----------------------------------------------+
| Tfidf      | charset  charset_error  | Transforms text documents to TF-IDF features |
|            | strip_accents lowercase |                                              |
|            | stop_words token_pattern|                                              |
|            | analyzer  max_df  min_df|                                              |
|            | max_features vocabulary |                                              |
|            | binary, ngram_range_min |                                              |
|            | ngram_range_max         |                                              |
+------------+-------------------------+----------------------------------------------+
| Lda        |                         |                                              |
+------------+-------------------------+----------------------------------------------+
| Lsi        |                         |                                              |
+------------+-------------------------+----------------------------------------------+
| Ntile      |                         |                                              |
+------------+-------------------------+----------------------------------------------+


.. note::
    
    You could add feature transformers to be used system wide in the `Predefined feature transformers page <http://cloudml.int.odesk.com/#/predefined/transformers>`_.
