==============
Exporting data
==============


Export vectorized data
======================

.. image:: ./images/export_vect_train_data.png

.. _export_test_examples_to_db:

Export test examples to database
================================

For exporting test examples to the database you need to:

* create :ref:`a predefined datasource <predefined-datasources>`  or `use <http://cloudml.int.odesk.com/#/predefined/datasources>`_ existing one.
* go to test details page and click to `Export Classification Results to DB` button
* in the form specify the datasource to be used to connect to the database, name of the table and fields, that should be imported.

.. note::

	Don't forgot, that test should be completed.

.. image:: ./images/export-to-db.jpg

.. _predefined-datasources:

Predefined DataSources
----------------------

Predefined DataSource stores the information about database connection. It could be used, when exporting tests examples
to specific database.

To create a new datasource navigate to `datasources page <http://cloudml.int.odesk.com/#/predefined/datasources/?action=add>`_
and fill the form with following attributes:

- `name` : string
	unique name of the datasource
- `type`: string, {'sql'}
	type of the database
- `vendor`: string, {'postgres'}
	the name of the database's vendor
- `conn` : string
	defined A connection string containing the DB connection details
