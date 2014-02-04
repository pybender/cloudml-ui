.. _import_handler:

===============================
Import handler JSON file format
===============================

Import handler aims to offer a flexible way for retrieving data from various data sources.

Now we have two types of import handlers:

* ``database`` -- it is used to describe database connection details, the query to execute, and instructions on which data should be extracted from the query and in which manner.
* ``request``

.. note::

	CloudML UI now supports only database datasources. Current version of the import handler will offer the functionality to extract data from single SQL queries. 


The extraction plan is a configuration file describing the data to be
extracted. It is a JSON object, with a specific structure.
An example of such file is the following::

	{
	  "target_schema":"bestmatch",
	  "datasource":[
	    {
	      "name":"cloudml",
	      "type":"sql",
	      "db":{
	        "conn":"host='localhost' dbname='cloudml' user='postgres' password='postgres'",
	        "vendor":"postgres"
	      }
	    }
	  ],
	  "queries":[
	    {
	      "name":"retrieve",
	      "sql": "SELECT * FROM table;",
	      "items": [
	        {
	          "source": "hire_outcome",
	          "process_as": "string",
	          "is_required": true,
	          "target_features": [
	            { "name": "hire_outcome" }
	          ]
	        },
	        { "source": "contractor_info",
	          "is_required": true,
	          "process_as": "json",
	          "target_features": [
	            { "name": "contractor.skills", "jsonpath": "$.skills.*.skl_name", "to_csv": true},
	            { "name": "tsexams", "jsonpath": "$.tsexams", "key_path": "$.*.ts_name", "value_path": "$.*.ts_score" }
	          ]
	        },
	        {
	          "process_as": "composite",
	          "target_features": [
	            { "name": "country_pair", "expression": {"type": "string", "value": "%(employer.country)s,%(contractor.dev_country)s"}}
	          ]
	        }
	      ]
	    }
	  ]
	}


.. note::

	You could find samples of import handlers files in 
	https://github.com/odeskdataproducts/cloudml-ui/blob/master/conf/

.. seealso::

	If you migrating your old import handler files take a look to
	:ref:`changes in json files <json_changes>`

So Import Handler Json file should countains following sections:

* ``target_schema`` - defines target schema name
* ``datasource`` - contains information about datasources (list). For more info about section go to the        :ref:`datasources section <features-datasources>`
* ``queries`` - contains information about queries (list). For more info about section go to the        :ref:`queries section <features-queries>`

.. _features-datasources:

Defining data sources
---------------------

This part of the configuration contains information about the database to
connect to in order to execute the query defined later. It may contain one map with the following fields:


============  ========   ===========
Name          Required   Description
============  ========   ===========
name          yes        A name uniquely identifying this database. In the future this should be required so that queries can refer to which DB connection to use for executing
type   		  yes        Currently only 'sql' is supported.
db.conn       yes        This is field 'conn' defined A connection string containing the DB connection details
db.vendor     yes        The name of the database's vendor. Currently only 'postgres' is supported.
============  ========   ===========

.. _features-queries:

Defining queries
----------------

The 'queries' section contains an array of objects describing each individual query. Currently only a single query is supported. Each query might contain the following fields:


============  ========   ===========
Name          Required   Description
============  ========   ===========
name          yes        A name uniquely identifying this query
sql   		  yes        The SQL query to execute. It may contain parameters to be replaced by user input (i.e. either coming from a HTTP request or command line option). These parameters must be in the form %(name)s.
items         yes        An array of objects describing which items (and how) to extract from each row in the query's result. The possible types of items is described below.
============  ========   ===========

Three types of query items are supported so far (``process_as`` field):

* ``identity``
* ``string`` - string query items, that read the value from a field defined in the SQL query, and store it to a single item
* ``float``
* ``boolean``
* ``integer``
* ``json`` -- JSON query items, that parse the data from a field and allow extracting multiple items using JSONPath expressions
* ``composite`` -- expression query items, which use data from other query items to produce new items


Query items have following parameters:

===============    ========   ===========
Name               Required   Description
===============    ========   ===========
source             yes        The name of the SQL query's field that contains the value to use
process_as         no        Represents item's type, that are listed before. If it isn't specified ``identity`` will be used.
is_required        no         Can be either true or false. Whether we require that resulting value is not null or empty string. In case it is set to true and no data is defined, the line will be ignored.
target_features    yes        A list of the features to extract. The resulting data will include a feature with name the target-feature's name, and value the value of the SQL query's field defined in source
===============    ========   ===========

Query target_features objects should contains parameters:

===============    ========   ===========
Name               Required   Description
===============    ========   ===========
name               yes        The name of the resulting feature
===============    ========   ===========


In case of ``json`` query items, the target_feature objects may contain the following fields:

====================    ========   ===========
Name                    Required   Description
====================    ========   ===========
name                    yes        The name of the resulting feature
jsonpath                yes        A JSONPath expression that dictates the location of the value.
to_csv                  no         Can be either true or false. If it is set to true and the result of the JSONPath expression is a list, it will be converted to a CSV value using ',' as a separator.
key_path, value_path    no         Both should contain a JSONPath expression. If both are defined, then a dictionary will be created as a value. key_path defines the expression for the dictionary's keys, while value-path defines the expression for the dictionary's value. Note that those two expressions are executed not on the entire JSON object, but on the part resulting from applying the expression in jsonpath.
====================    ========   ===========

Finally, the ``expression`` item target_features objects may contain the following fields:

====================    ========   ===========
Name                    Required   Description
====================    ========   ===========
name                    yes        The name of the resulting feature
expression              yes        A string expression describing how the resulting value will be formatted. The string may include parameters in the format %(name)s. Possible values for name might be any feature extracted in previous query items. If any of the input parameters is not set, then the result will be null
====================    ========   ===========