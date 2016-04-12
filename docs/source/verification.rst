.. _model-verification:

==================
Model verification
==================

Model verification - is a tool, which makes possible to verify the model, deployed to the predict server.

List of the model verifications could be found on  `this page <http://cloudml.int.odesk.com/#/predict/verifications>`_.

Creating new verification
=========================

To create a new verification click to the "Add new verification" button. In the dialog it needed to specify:

* server - cloudml-predict server.
* predict import handler, which deployed to specified server. This import handler also defines the CloudML model, which also should be deployed to this server.
* data - successfully passed CloudML model test with test examples. This test examples would be iterated while model verification.
* count - specifies how many test examples would be used.
* predict class - predict command to be used
* parameters map - specifies how to map command parameters to the data from the test example.
  
Predict Commands
----------------

You could use any predict command from predict-utils project. When it choosed a predict command you will need to map the command options to test example fields. When calling this command also following options would be added:

* -c - path to config file (it depends on type of the predict-server and is different for production, staging and dev servers).
* -i - importhandler name which was specified
* -p - version of the cloudml-predict: 'v3' 

Also it possible to choose "Other" option in predict class select. In this case no predict commands would be used and the data from test example would be posted to the predict server.

Mapping parameters
------------------

When choosing the predict-utils command it needed to map command arguments to the test example fields.

When choosing "Other" as predict class, it needed to map predict import handler's import parameters to test example fields.

Model Verification
==================

Following metrics calculating while model verification:

* count of the errors, for example bad requests, etc.
* max response time of the predict server
* count of the valid label predictions
* count of the same probability as in the test example prediction

Also it created a list of the zero features.
Zero feature is the feature which have zero  vectorized value in all predict server responses.

Also it possible to iterate over verification examples to compare test example results with predict server response.

Verification Example
--------------------

Verification Example details contains following information:

* Data - data, which was posted to predict server
* Response Time - predict server response time
* Vectorized values from the test example and from the predict server response.
  
.. note::

	In Result tab present all response of the predict server.
