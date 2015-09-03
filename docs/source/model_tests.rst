.. _test_metrics:

====================
Evaluating the Model
====================

After testing the model user gets a set of test metrics.

There are two types of the models:

* classification
* regression

So for classification models would be available :ref:`classfication metrics <classifier_test_metrics>`, for regression - :ref:`regression metrics <regression_test_metrics>`.

They could be found in the `Metrics` tab of the Test details. Confusion Matrics would be displayed in the separate tab.

.. _classifier_test_metrics:

Classifier Test Metrics
=======================

This metrics would be available for classifiers:

* Logistic Regression
* Stochastic Gradient Descent Classifier
* Decision Tree Classifier
* Gradient Boosting Classifier
* Extra Trees Classifier
* Random Forest Classifier

Classification Accuracy
-----------------------

The classification accuracy depends on the number of test examples correctly classified (true positives plus true negatives) and is evaluated by the formula:

.. image:: ./_static/models/accuracy.gif

where t is the number of sample cases correctly classified, and n is the total number of test examples.

Receiver operating characteristic
---------------------------------

Receiver Operating Characteristic (ROC) metrics used to evaluate classifier output quality.

ROC curves typically feature true positive rate on the Y axis, and false positive rate on the X axis. This means that the top left corner of the plot is the “ideal” point - a false positive rate of zero, and a true positive rate of one. This is not very realistic, but it does mean that a larger area under the curve (AUC) is usually better.

For binary classification we will have one 
The Area Under an ROC Curve and for multiclass classification we will have one for each class.

Above each ROC curve also The Area Under an ROC Curve displayed.

Confusion Matrix
----------------

Confusion Matrix (Matrixes in case of multiclassification) would be available in "Confusion Matrix" tab in test details page. It appears after test would be successful completed.

Precision Recall Metrics
------------------------

* Avarage Precision
* Precision Recall curve

.. note::

	Precision Recall Metrics are available only for binary classification.


.. _regression_test_metrics:

Regression Test Metrics
=======================

Support vector regression tests will have following metrics:

+------+------------------------+
| Name | Description            |
+======+========================+
| rsme | Root square mean error |
+------+------------------------+
