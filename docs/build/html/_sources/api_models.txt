Models
======

+--------+---------------------------------------------------------------+--------------------+
| Method | Resource                                                      | Description        |
+========+===============================================================+====================+
| GET    | :ref:`/cloudml/model/<list_models>`                           | Get list of models |
+--------+---------------------------------------------------------------+--------------------+
| GET    | :ref:`/cloudml/model/:ModelName<get_model>`                   | Get model by name  |
+--------+---------------------------------------------------------------+--------------------+
| POST   | :ref:`/cloudml/model/:ModelName/:HandlerName/predict<predict>`| Predict            |
+--------+---------------------------------------------------------------+--------------------+


Upload Model
------------

* Method: POST
* URL: /cloudml/model/:ModelName/

Examples
^^^^^^^^

 curl -X POST -F "trainer=@/data/models/model.autohde.v1.20121025.20121028" -F importhandler="$(cat /home/papadimitriou/odeskdev-cloudml/models/bestmatch/autohide/extract.v1.json)"  "http://172.27.77.141/api/cloudml/model/BestMatch.Autohide.vv1.w2"
 

.. _list_models:

List of Models
--------------

* Method: GET
* URL: /cloudml/model/

Response Parameters
^^^^^^^^^^^^^^^^^^^

* models - List of models


Errors
^^^^^^

404 Not Found::

    {
      "response": {
        "server_time": 1364714381.157842, 
        "error": {
          "status": 404, 
          "debug": null, 
          "message": "Model doesn't exist", 
          "code": 1001
        }
      }
    }

Example
^^^^^^^

cURL::

    curl http://127.0.0.1:5000/cloudml/model/

Response body::
    
    {
        "models": [
            {
                "name": "test",
                "status": "Trained",
                "created_on": "2013-03-28T05:47:46.566463"
                ...
            }
        ]
    }
    


.. _get_model:

Get Model
---------

* Method: GET
* URL: /cloudml/model/:ModelName

Request paraneters
^^^^^^^^^^^^^^^^^^

* ModelName - name of model


Response Parameters
^^^^^^^^^^^^^^^^^^^

* id - internal id of model
* name - name of model
* status - status of model [New, Trained]
* created_on - date and tiome of create
* importhandler - importhandler for testing model
* target_variable - target variable

Errors
^^^^^^

404 Not Found::

    {
      "response": {
        "server_time": 1364714381.157842, 
        "error": {
          "status": 404, 
          "debug": null, 
          "message": "Model doesn't exist", 
          "code": 1001
        }
      }
    }

Example
^^^^^^^

cURL::

    curl http://127.0.0.1:5000/cloudml/model/test

Response body::
    
    {
        "model": {
            "name": "test",
            "status": "Trained",
            "created_on": "2013-03-28T05:47:46.566463"
            ...
        }
    }


.. _predict:

Predict
-------

* Method: POST
* URL: /cloudml/model/:ModelName/:ImporthandlerName/predict

Request paraneters
^^^^^^^^^^^^^^^^^^

* ModelName - name of model

Response Parameters
^^^^^^^^^^^^^^^^^^^

Errors
^^^^^^
400 Bad Request::



    {
      "response": {
        "server_time": 1364714887.802514, 
        "error": {
          "status": 400, 
          "debug": null, 
          "message": "400 Bad Request", 
          "code": 1005
        }
      }
    }

404 Not Found::

    {
      "response": {
        "server_time": 1364714381.157842, 
        "error": {
          "status": 404, 
          "debug": null, 
          "message": "Model doesn't exist", 
          "code": 1001
        }
      }
    }

Example
^^^^^^^

cURL::

    curl -XPOST http://127.0.0.1:5000/cloudml/model/1111/qqqq/predict \
    --data-urlencode 'hire_outcome=1'
    --data-urlencode 'application=app'
    --data-urlencode 'opening=232'
    --data-urlencode 'employer_info={"country": "Ukrain","op_timezone": "GMT2","op_country_tz": "GMT1"}'\
    --data-urlencode 'contractor_info={"country": "Ukrain","dev_timezone": "dev_timezone"}'


Response body::
    
  { 
    "prob": 0.5167695219179442,
    "label": 0
  }

