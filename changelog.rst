.. _changelog:

Changelog
=========

Relese 2013-05-27
-----------------
* Feature - Added button for reload weights


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
