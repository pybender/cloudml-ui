.. _features:

========================
Feature json file format
========================

It includes information like:

1. The classifier's configuration.
2. The features (and their name).
3. The type of each feature. This might imply transformation to be done on each item of data.
4. Generic feature types, in case more than one feature share the same feature type.
5. Transformers, that allow converting features to different formats (i.e. Tfidf for converting a text feature to a matrix of TF-IDF features).


.. warning::

	If you migrating your old import handler files take a look to
	:ref:`changes in json files <json_changes>`
