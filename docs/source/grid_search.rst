
Model Parameters Grid Search
============================

Searches over specified parameter values for an classifier.
As the underlying implementation used `Scikit GridSearchCV <http://scikit-learn.org/stable/modules/generated/sklearn.grid_search.GridSearchCV.html#sklearn-grid-search-gridsearchcv>`_

For starting parameters grid search click to "Grid search" button on the right-top corner of the model details page.

In opened popup you should choose classifier parameters, dataset for training, dataset for testing and model evaluation metrics.

.. image:: ./_static/getting_started/grid-search.png

Searching the best classifier parameters is the background process, so navigate to "Parameters Search" tab to view results:

.. image:: ./_static/getting_started/grid-search-results.png

Seems the best parameters are "C: 100, penalty: l2".