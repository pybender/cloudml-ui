.. _test_metrics:

============
Test Metrics
============

After testing the model user gets a set of test metrics.
Different 
:ref:`classifier <classifier>`
has different metrics.

.. classifier_test_metrics:

Classifier Test Metrics
-----------------------

Logistic regression and stochastic gradient descent classifier's tests will have following metrics:

+------------------------+------------------------+
| Name                   | Description            |
+========================+========================+
| roc_curve              | ROC curve              |
+------------------------+------------------------+
| roc_auc                | Area under ROC curve   |
+------------------------+------------------------+
| confusion_matrix       | Confusion Matrix       |
+------------------------+------------------------+
| accuracy               | Accuracy               |
+------------------------+------------------------+
| avarage_precision      | Avarage Precision      |
+------------------------+------------------------+
| precision_recall_curve | Precision-recall curve |
+------------------------+------------------------+


.. regression_test_metrics:

Regression Test Metrics
-----------------------

Support vector regression tests will have following metrics:

+------+------------------------+
| Name | Description            |
+======+========================+
| rsme | Root square mean error |
+------+------------------------+
