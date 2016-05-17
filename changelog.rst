.. _changelog:

Changelog
=========


Release 2016-05-17
------------------
* Bug - Target variable is always required now, fixed possibility to make it not required
* Bug - Cut error message on dataset import
* Bug - Fixed train transformer dialog issue + support automatic update of training status
* Bug - Fixed deleting test and dataset while they is in progress
* Task - Server sorting by name
* Task - Upload to predict and update file there in one action
* Bug - Reload model classifier properties if predefined classified is selected and saved


Release 2016-05-03
------------------
* Feature - Added possibility to download xml of ih
* Bug - Don't allow to edit entities of import handler created by another user
* Bug - Fixed server model verification form issues
* Bug - Fixed amazon settings configuration issues between cloudml and cloudml ui
* Task - Link to dataset importing logs from model training/testing logs
* Bug - Don't allow to train model when test is not finished
* Bug - Fixed dataset import error
* Bug - Fixed updating model issues: model was not relevant in some scenarios
* Task - Load necessary tabs when model train/test is completed
* Bug - Fixed not relevant values appearing in group by section
* Task - Added link to server logs
* Task - Added page title
* Feature - Server Model Verification
* Feature - word2vec and doc2vec transformers support
* Feature - Support python scripts (part of xml import handler) in separate files (local or amazon)
* Task - Added preview of python script
* Bug - Production server settings can be modified only by admins
* Task - Save import handler's XML to dataset on import
* Task - Block modifying deployed import handlers, models and datasets that were used on deployed model train/test
* Task - Add dataset name and id to training logs
* Bug - Fix some form inputs names on ui
* Bug - Fixed confusion matrix recalculation and layout for more that 10 labels
* Task - Allow editing model features in JSON view
* Bug - Fixed error messages appearing after changed in input-editable elements
* Bug - Fixed python True and xsd true error in pig datasource
* Bug - Fixed model visualisation tree displaying freeze
* Bug - Cut amazon credentials and logins/passwrods in datasources on import handler cloning
* Bug - Set import handler user on cloning
* Task - Check and parse feature default date
* Feature - Support confusion matrix calculation for multi-class models
* Bug - Fixed predefined classifier save issues
* Feature - Displaying celery logs for each confusion matrix recalculation
* Bug - Fixed test examples pagination
* Bug - Added validation of python script on posting
* Feature - Added ordering of model and import handler lists (by Name, Updated on)
* Bug - Fixed aws instance editing
* Bug - Fixed alert on scaler editing



Relese 2013-09-09
-----------------
* Bug - UnicodeEncodeError during run_test
* Bug - Tests list should be updated after deleting test
* Bug - Fixed dataset name editing
* Bug - Remove links to dataset when deleting
* Bug - Tag's "count" field isn't updated after model was deleted
* Task - Added manual upload dataset to s3
* Task - Added multipart upload dataset to s3
* Task - Improve train dialog
* Task - Tests improvements
* Taks - Adding dashboard page and API for getting some stat data
* Taks - Humanize time format
* Feature - Sort examples by probability
* Feature - Adding filtering to models list
* Feature - Added using exsiting file datset instead download from s3
* Feature - Generating download from s3 dataset url only when user clicks download btn
* Support - Added generating xunit report
* Support - Celery version updated
* Support - Added coverage report command
* Support - Documentation updated


Relese 2013-08-16
-----------------
* Bug - Fixed running test with importing dataset
* Bug - Reset error message before open test dialog
* Bug - Restore ordering weights on column view
* Feature - Using multiple datasets for train model


Relese 2013-08-13
-----------------
* Bug - Fixed storing examples to s3
* Task - Store test examples to s3 the default only for very big datasets
* Taks - Added select for 'Examples label field name' and
'Examples id field name' fields on model details page
* Feature - Add oDesk auth


Relese 2013-08-01
-----------------
* Bug - Fixed upload model
* Task - Store TestExamples on s3
* Feature - Added log levels filter


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
