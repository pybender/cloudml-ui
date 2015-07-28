========
Settings
========


DB settings
-----------

SQLALCHEMY_DATABASE_URI
~~~~~~~~~~~~~~~~~~~~~~~

The database URI that should be used for the connection. Examples:

postgresql://username:password@server/db


SQLALCHEMY_DEBUG
~~~~~~~~~~~~~~~~

Is set to True SQLAlchemy will enable debug mode.


SQLALCHEMY_ECHO
~~~~~~~~~~~~~~~

If set to True SQLAlchemy will log all the statements issued to stderr which can be useful for debugging.

SQLALCHEMY_RECORD_QUERIES
~~~~~~~~~~~~~~~~~~~~~~~~~

Can be used to explicitly disable or enable query recording. Query recording automatically happens in debug or testing mode.

.. note:: For detalized information please look https://pythonhosted.org/Flask-SQLAlchemy/config.html

Amazon settings
---------------

Need AWS credentials for get access to AWS S3, EC2, DynamoDB services.

 - AMAZON_ACCESS_TOKEN
 - AMAZON_TOKEN_SECRET
 - AMAZON_BUCKET_NAME

.. note:: Please also look http://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSGettingStartedGuide/AWSCredentials.html for more details.

Upwork settings
--------------



- ODESK_OAUTH_KEY
- ODESK_OAUTH_SECRET

.. note :: 
	For creating new upwork api keys please go to https://www.upwork.com/services/api/apply . See the list of your registered keys -https://www.upwork.com/services/api/keys .

Main settings
-------------

DATA_FOLDER
~~~~~~~~~~~

Folder for temprary saving datasets. 


EXAMPLES_CHUNK_SIZE
~~~~~~~~~~~~~~~~~~~

Number of examples in chunk for store examples to s3


MULTIPART_UPLOAD_CHUNK_SIZE
~~~~~~~~~~~~~~~~~~~~~~~~~~~



BROKER_URL
~~~~~~~~~~

Celery broker url


CELERY_RESULT_BACKEND
~~~~~~~~~~~~~~~~~~~~~

Celery result backend


REQUESTING_INSTANCE_MAX_RETRIES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Max retries when request spot instance


REQUESTING_INSTANCE_COUNTDOWN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Timeout between retries request spot instance
