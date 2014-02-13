.. _get_started:

************************
Get Started With CloudML
************************

CloudML aims to provide a set of tools that allow building a classifier on the cloud. 

CloudML UI is user iterface, that simplyfies using CloudML.
It countains following entities:

1. Models, which receives data from the import handler and trains a classifier to produce a classification model. Then user could run tests for models to compare metrics and real data with predicted one.
2. Import handlers, that are responsible for feeding the model and tests with data.
3. Instances, that represents AWS Instances to be used in model training and tests.
4. Predefined entities (classifiers, datasources, feature transformers, scalers, etc.)


Creating the import handler
===========================

For creating new import handler you need to navigate to `this page <http://cloudml.int.odesk.com/#/importhandlers/add>`_. You need to define unique name and could upload import handler json file (format is described 
:ref:`here <import_handler>`).

Loading the dataset
-------------------

You could create a dataset to be used for model training/testing by clicking `Import DataSet` in import handler details page. You need to specify import handler parameters (from sql query) and dataset format. 


Creating the model
==================

The could creating the model by adding new model or uploading untrained one.

New model
---------

For creating new untrained model you need to navigate to Add new model page: http://cloudml.int.odesk.com/#/add_model
Model name (should be unique) and import handlers are required.
You could choose import handler from a lise or specify json file (format is described 
:ref:`here <import_handler>`)
You could also specify features.json file if you have.
Json file format is described 
:ref:`here <features>`


Upload your model
-----------------

For uploading the model you need to navigate to Add new model page: http://cloudml.int.odesk.com/#/upload_model
Model name (should be unique) and import handlers are required.
You could choose import handler from a lise or specify json file (format is described 
:ref:`here <import_handler>`)
Also defining model file is required. It's pickled trainer class. You could download model trainer from existing model by clicking "download trainer" in model details page.


Model details
-------------

The information about model organizes to few tabs:

- Model - contains info about classifier and model features.
- Training - contains status and resources, that used for training model. Also includes the information about feature weights for the `Trained` model.
- Tests
- About - all other info about models.


Testing the model
=================

The user could perform testing of the trained model by clicking `Run test` in model details page. Then user should to either define datasets containing data to be used for testing the model, or specify the required parameters to invoke the import handler and retrieve the data. Also he/she need to define instance that would be used for processing test.

The result of the test is a set of metrics and a data with predicted and actual values and feature weights. More information could be found in
:ref:`here <test_metrics>`
