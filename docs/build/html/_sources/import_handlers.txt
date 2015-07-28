Importing the Data
==================


.. contents:: 
   :depth: 4

Entities and Fields
-------------------

Testing the query
~~~~~~~~~~~~~~~~~

For database datasources you could run the entity's sql query by clicking to "Run Query" button. In the dialog you will need specify datasource to be used, query parameter and count of the rows to display.

.. image:: ./_static/import_handlers/test-query-popup.png

.. image:: ./_static/import_handlers/test-query-results.png

Autoload fields
~~~~~~~~~~~~~~~

When you set "Autoload Fields" checkbox, the subentities and fields will be created in the importhandler automaticaly by analyzing sql query results row:

.. image:: ./_static/import_handlers/autoload-fields.png
