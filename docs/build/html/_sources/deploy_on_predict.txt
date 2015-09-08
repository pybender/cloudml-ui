.. _deploy_on_predict:

========================================================
Deployment the model or import handler to predict server
========================================================

Uploading to predict server
---------------------------

You could upload model or import handler to predict server by clicking to  "Upload for Predict" button in the details page.

For example model details page:

.. image:: ./_static/servers/upload-model1.png
   :width: 800px


In popup you will need to
specify the server.

.. image:: ./_static/servers/upload-model2.png

.. note::

    List of available servers you could find in the `server list page <http://cloudml.int.odesk.com/#/servers>`_.

Reloading the model or import handler on predict server
-------------------------------------------------------

To use the uploaded model in predict you need to reload the model on the predict server. For it go to the server details page. Find corresponding model or import handler in the list and click on "reload" button in the actions column. 

.. image:: ./_static/servers/upload-model3.png

.. note::

    If you moved model/import handler file to Amazon S3 manually, you could simply find it in corresponding server details page and load it to use for predict (by clicking to reload button).

If you need different name on predict, you can rename model.

For checking new model on predict:
	
	$ curl http://your_server_url/cloudml/v1/model/

Example of response:

	{
	  "models": [
	    {
	      "created": {}, 
	      "name": "somemodel1", 
	      "schema-name": "bestmatch"
	    }, 
	    {
	      "created": {}, 
	      "name": "somemodel2", 
	      "schema-name": "bestmatch"
	    }
	  ]
	}

Deleting the model or import handler file
-----------------------------------------

You can delete the model or import handler file from predict by clicking to delete button in models/import handlers files table in server details page.

.. note::

    Actually system doesn't delete the model or import handler from Amazon S3.
    It sets metadata's key 'hide', so the model or import handler becomes invisible in CloudML UI and unavailable in CloudML Predict.
