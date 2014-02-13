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


Creating the model
==================

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