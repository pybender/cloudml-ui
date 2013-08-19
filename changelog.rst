.. _changelog:

Changelog
=========


Relese 2013-08-16
-----------------
* Bug - Fixed running test with importing dataset
* Bug - Reset error message before open test dialog
* Bug - Restore ordering weights on column view
* Feature - Using multiple datasets for train model


Relese 2013-08-13
-----------------
* Feature - Add oDesk auth
* Task - Store test examples to s3 the default only for very big datasets
* Bug - Fixed storing examples to s3
* Taks - Added select for 'Examples label field name' and
'Examples id field name' fields on model details page


Relese 2013-08-01
-----------------
* Bug - Fixed upload model
* Feature - Added log levels filter
* Task - Store TestExamples on s3


Relese 2013-07-22
-----------------
* Task - Added some field to dataset details
* Feature - Add cancel request button 
* Feature - Add 'Requesting spot instance' and 'Instance started' to model


Relese 2013-07-11
-----------------
* Bug - Fixed and improved validation json files
* Task - Changed delimeter to ',' in csv export
* Task - Added support local config


Relese 2013-07-10
-----------------
* Task - Changed gunicorn timeout
* Bug - Fixed loading weights on column view after each changing view


Relese 2013-07-09
-----------------
* Bug - Added cathing when model have only negative weights in fill_model_parameter_weights task
* Bug - Fixed paging on weights tab


Relese 2013-07-04
-----------------
* Feature - Added option to choose which fields should be included in the csv


Relese 2013-07-03
-----------------
* Feature - Added request spot instance for training model


Relese 2013-06-24
-----------------
* Feature - Added log pagination
* Task - Delete log when delete related object
* Bug - Display in run test and train model popup only successfully imported datasets
* Task - Made “Metrics” the default screen on test details
* Task - Make possible to upload import handler file (not choose from list) when upload/add new model


Relese 2013-06-18
-----------------
* Feature - Added storing datasets to s3
* Feature - Added compressing dataset
* Feature - Updated model/test status when importing dataset in separete task 


Relese 2013-06-13
-----------------
* Task - Reorganized model details tabs
* Feature - Added a button to delete an import handle and dataset
* Bug - Restored link to examples on test list
* Task - Display train/test/load data logs without using event source
* Feature - Added dataset details


Relese 2013-06-09
-----------------
* Feature - Moved importing data to separate task
* Feature - Added storing datasets
* Feature - Added list of instances wich use for training/testing


Relese 2013-05-27
-----------------
* Feature - Added button for reload weights
* Bug - Fixed storing examples
* Feature - Made clickable links on MAP page


Relese 2013-05-17
-----------------
* Feature - Added to model property "id example" and "label example"
* Feature - Move storing weights to celery task
* Support - Updated pymongo


Relese 2013-05-14
-----------------
* Feature - Added search weights
* Feature - Added weights tree view
* Feature - Added download models, inport handlers
* Feature - Added show logs in ui when model are testing, training
 

Relese 2013-05-07
-----------------

* Suppprt - Moved to separate repo
* Suppprt - Improve deploy script (now ui rebuild on instance) (please update fabdeploy)
* Feature - Changed MAP page: add n param
* Feature - Changed confusion matrix page: make the counts clickable 


Relese 2013-04-01
-----------------

* Feature - Add predict api
* Suppprt - Add docs for api
* Feature - Add request import handler


Release 2013-03-25
------------------

* Feature - Add compare models
* Support - Update docs
* Feature - Move all management commands to manage.py


Release 2013-03-20
------------------

* Support - Create docs
* Feature - Add upstart for autostart supervisord
* Feature - Add flower for monitoring celery

Release 2013-03-19
------------------
* Feature - Use celery for testing and training models
