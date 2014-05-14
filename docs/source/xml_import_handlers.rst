.. _xml_import_handlers:

===================================
Generic Import Handler Format (XML)
===================================

CloudML predict uses two different approaches for importing data:

- **DB Import Handler** is used for importing data from database while training a classifier. Although we refer it as a "database" handler, we'd like to add functionality for importing data from additional data sources, like:
    * CSV files
    * HTTP with JSON or XML data
    * Files containing a JSON document per row
- **Web Import Handler** is used for importing data and feeding them to a trained classifier in order to get result.

Both handlers may need to perform some transforming logic on their
import in order to produce the final results.

Although both handlers prepare data for the same classification model,
their formats are different. The goal of this document is to describe a
new format that can be used for both handlers.

The new format will be in XML format, from JSON format currently in
production. The rest of the document provides details of the format.

Top level element
-----------------

Top level element is ``<plan>``. There's no attributes expected for this
element. Plan may contain the following elements:

- :ref:`script <script>` (any)
- :ref:`inputs <inputs>` (one or zero)
- :ref:`datasources <datasources>` (exactly one)
- :ref:`import <import>` (exactly one)
- :ref:`predict <predict>` (should be present only if we are in testing mode).

.. _script:

Script
------

A ``script`` element is used to define python functions that can be
used to transform data. Code inside the script tag will be added
whenever a python function is call. It is a good idea to wrap
scripts in <![CDATA[ ...]]> elements.

Example::

    <script>
    <![CDATA[
        def intToBoolean(a):
            return a == 1
    ]]>
    </script>

It is also possible to reference external Python files. This can be
done to ease development. Scripts should be expected in the same
directory as the XML file.

Example::

    <script src="functions.py" />

.. note::

    Scripts from external python files functionality is not implemented yet.

.. _inputs:

Inputs
------

Tag ``<inputs>`` groups all input parameters required to execute the import handler. Input parameters are defined in ``<param>`` tags.

Each param may have one of the following attributes:

- ``name`` (**required**) - the name of the parameter.
- ``type`` - the type of the input parameter. If ommited, it should be considered string.
- ``format`` - formating instructions for the parameter (i.e. date format etc).
- ``regex`` - a regular expression that can be used to validate input parameter value

.. note::

    Format could be applied only to the date input parameter using python's `strptime` method. More details about format string could be found in 
    `python documetation <https://docs.python.org/2/library/datetime.html#strftime-and-strptime-behavior>`_

Example::

    <inputs>
        <!-- Define an integer parameter. Use regex to dictate only positive integers -->
        <param name="application" type="int" regex="\d+" />

        <!-- Date parameter with instructions on how to interpret date-->
        <param name="year" type="date" format="%Y"/>

        <!-- Boolean parameter -->
        <param name="only_fjp" type="boolean" />
    </inputs>


.. _datasources:

Datasources
-----------

Data is fed to the system using various datasources. The ``<datasources>`` part of the handler contains the connection details.

Datasources may be:

- ``Database connections``
- ``CSV files``
- ``HTTP GET/POST``
- ``Hadoop with Pig``
- ``...`` (more to be added)

Datasources are identified by their unique names and can be accessed by
at any point in the file. Each datasource is using a different tag to
configure it.

Database connections
~~~~~~~~~~~~~~~~~~~~

Database connections can be defined either by directly inserting the
connection details or by referencing a named connection. In both cases,
the element used is ``<db>``.

Here are the possible attributes:

- ``name`` (**required**) - a unique name for this datasource
- ``name-ref`` - a reference to the named connection (not supported now)
- ``host`` - the name of host to connect to
- ``dbname`` - the database name
- ``user`` - the username to use for connecting to the database
- ``password`` - the password to use for connecting to the database
- ``port`` - the port number to connect to at the server host
- ``vendor`` - the DB's vendor (mysql, postgres etc)


Note that name is required in both cases. For named connections, only name-ref should be also present. When defining the DB connection details in handler's file, name-ref, host, dbname and vendor should be present.

Examples::

    <!-- 
    -- Defines a named connection with name "namedDBConnection" 
    -- that uses connection details defined in myODWConnection.
    -->
    <db name="namedDBConnection" name-ref="myODWConnection" />

    <!-- Defines a database connection. -->
    <db name="odw" 
        host="localhost"
        dbname="odw"
        user="postgres"
        password="postgres"
        vendor="postgres" />

.. note::

    Named connections aren't implemented yet.


CSV files
~~~~~~~~~

CSV file can be used for importing data from local files. It is possible
to reuse headers from CSV file, or define aliases for the column names
in the import handler.

The related tag is ``csv``, and the possible attributes are:

- ``name`` (**required**) - a unique name for this datasource
- ``src`` (**required**) - the path to the CSV file

Header information can be defined by adding child ``<header>`` elements
to the ``<csv>`` element. Each ``<header>`` element must contain exactly
two fields:

- ``name`` - the name of the column
- ``index`` - the column's index (columns are zero-indexed).

Examples::

    <!-- Defines a CSV datasource with headers in file. -->
    <csv name="csvDataSource" src="stats.csv" />

    <!-- Defines a CSV datasource with headers in handler. -->
    <csv name="csvDataSource" src="stats.csv">
        <!-- Note that some columns are ignored -->
        <header name="id" index="0" />
        <header name="name" index="2" />
        <header name="score" index="7" />
    </csv>


HTTP
~~~~

HTTP requests are used for importing JSON data from remote HTTP
services.

The tag used for defining them is ``<http>``, and the possible attributes are:

- ``name`` (**required**) - a unique name for this datasource
- ``method`` - the HTTP method to use (GET, POST, PUT, DELETE - default is GET)
- ``url`` (**required**) - the base URL to use

Example::

    <http name="jar"
        method="GET"
        url="http://d-postgres.odesk.com:11000/jar/" />

When using this datasource with RESTful services, try to define the base
URL. If you need to query for specific entities, you can define query
parameters later during the import phase.


Pig
~~~

Pig is a tool for analyzing large data sets based on Hadoop. Pig Latin
is the language that allows querying and/or transforming the data. A Pig
datasource is a connection to a remote Hadoop/Pig cluster. It is defined
using ``<pig>`` tag. Possible attributes are:

- ``name`` (**required**) - a unique name for this datasource
- ``connection`` (**required**) - connection to Hadoop/Pig cluster
- ``jobid`` (optional) - define job flow id, if you want to use existing cluster
- ``amazon_access_token`` (**required**)
- ``amazon_token_secret`` (**required**)
- ``pig_version`` (optional)
- ``bucket_name`` (optional) - Amazon S3 bucket name for saving results, logs, etc.
- ``ec2_keyname`` (optional) - EC2 key used for the instances
- ``keep_alive`` (optional)(bool) – Denotes whether the cluster should stay alive upon completion
- ``hadoop_params`` (optional)
- ``num_instances`` (optional) – Number of instances in the Hadoop cluster
- ``master_instance_type`` (optional) - EC2 instance type of the master
- ``slave_instance_type`` (optional) – EC2 instance type of the slave nodes



Example::

    <pig name="pig3" jobid="job-id" amazon_access_token="token" amazon_token_secret="secret"/>

For store results we should use '$output' parameter as output dir. For example::

    C = FOREACH B GENERATE application, opening;
    STORE C INTO '$output' USING JsonStorage();

.. _import:

Import
------

After defining the datasources, the import handler need to define how to
translate data from each datasource input. This is done within the
``<import>`` element. In order to be able to understand how the mapping
is done, we need to introduce the concept of entity.

An entity models data coming from various datasources. I.e. an entity
might describe the data coming from a database table or view. Each
entity is associated with a datasource and (possibly) some query
parameters. For example, a database entity might use a SQL query, while
an HTTP entity might add some path and query parameters to the
datasource's URL. An entity describes multiple entity "instances". I.e.
if an entity describes a database table, an entity "instance" describes
a row in the database.

An entity is defined using the ``<entity>`` tag. The possible attributes
of the element are the following:

- ``name`` (**required**) - a unique name to identify the entity
- ``datasource`` (**required**) - the datasource to use for importing data
- ``query`` - a string that provides instructions on how to query a datasource (i.e. a SQL query or a path template). Queries can be also defined as child elements (to be discussed later).

Examples::

    <!-- An entity that uses a DB connection -->
    <entity name="employer" datasource="mysqlConn" query="SELECT * FROM table">
        ...
    </entity>

    <!-- An entity that uses an HTTP datasource -->
    <entity name="employer" datasource="odr" query="opening/f/#{opening}.json">
        ...
    </entity>


Queries
~~~~~~~

The first possible child of a ``<entity>`` is a query. This can be used
to improve readability of the XML file and replace the query attribute
of the entity. It is also useful if the query doesn't return data, but
actually triggers data calculation. Examples of such cases include
running a set of SQL queries that create tables or executing a Pig
script. In this case, attribute ``target`` needs to be defined inside
the ``<query>`` tag. The value of this attribute provides details on
where to look for the actual data.

Examples::

    <!-- An entity that uses a DB connection -->
    <entity name="employer" datasource="mysqlConn">
        <query>
            <![CDATA[
                SELECT *
                FROM table t1 JOIN table t2 ON t1.id = t2.reference
                WHERE t2.creation_time < '#{start_date}'
            ]]>
        </query>
        ...
    </entity>

    <!-- An entity that uses an HTTP datasource -->
    <entity name="employer" datasource="odr">
     <query>
            <![CDATA[
                opening/f/#{opening}.json
            ]]>
        </query>
        ...
    </entity>


Query strings depend on the datasource:

- Database datasource requires SQL queries.
- HTTP datasources can add values to the path. 
- CSV datasources do not support queries.

It is possible to use variables in queries using the notation ``#{variable}``. This will be replaced either by an input parameter with name equal to the variable.


Fields
~~~~~~

Fields are used to define how to extract data from each entity
"instance". They are defined using the ``<field>`` tag, and can define
the following attributes:

- ``name`` (**required**) a unique name for the field
- ``column`` - if entity is using a DB or CSV datasource, it will use data from this column
- ``jsonpath`` - if entity is a JSON datasource, or field type is json, it will use this jsonpath to extract data
- ``type`` - can be integer, boolean, string, float or json. If defined, the value will be converted to the given type. If it's not possible, then the resulting value will be null.
- ``key_path`` - a JSON path expression for identifying the keys of a map. Used together with ``value_path``
- ``value_path`` - JSON path expression for identifying the values of a map. Used together with ``key_path``. 
- ``regex`` - applies the given regular expression and assigns the first match to the value
- ``split`` - splits the value to an array of values using the provided regular expression
- ``dateFormat`` - transforms value to a date using the given date/time format
- ``join`` - concatenates values using the defined separator. Used together with ``jsonpath`` only.
- ``template`` - used to define a template for strings. May use variables.
- ``script`` - call the python script defined in this element and assign the result to this field. May use any of the built-in functions or any one defined in a `Script <>`_ element. Variables can also be used in script elements. Also could be defined as inner <script> tag.
- ``transform`` - transforms this field to a datasource. For example, it can be used to parse JSON or CSV data stored in a DB column. Its values can be either ``json`` or ``csv``.
- ``headers`` - used only if ``transform="csv"``. Defines the header names for each item in the CSV field.
- ``required`` - whether this field is required to have a value or not. If not defined, default is false.

Examples::

    <!-- HTTP JSON entity -->
    <entity name="jar_application" datasource="jar" query="get_s/#{employer}/#{application}.json">
        <field name="ja.bid_rate" type="float" jsonpath="$.result.hr_pay_rate" />
        <field name="ja.bid_amount" type="float" jsonpath="$.result.fp_pay_amount" />
        <field name="opening.pref_count" type="int" jsonpath="$.result.job_pref_matches.prefs_match" />
        <field name="application.creation_time" jsonpath="$.result.creation_time" dateFormat="YYYY-mm-DD" />

    </entity>

    <!-- HTTP JSON entity -->
    <entity name="contractor" datasource="odr" query="opening/f/#{opening}.json">
        <field name="contractor.skills" path="$.skills.*.skl_name" join="," />
        <field name="contractor.greeting" template="Hello #{contractor.name}" />
        <field name="matches_pref_english" script="#{contractor.dev_eng_skill}> #{pref_english})" />
    </entity>

    <!-- DB entity -->
    <entity name="dbentity" datasource="mysqlConnection">
        <query>
            <![CDATA[
                SELECT *
                FROM table t1 JOIN table t2 ON t1.id = t2.reference
                WHERE t2.creation_time < '#{start_date}'
            ]]>
        </query>
        <field name="id" column="t1.id" />
        <field name="name" column="t1.full_name" />
        <field name="category" column="t2.category" />
        <field name="active" type="boolean" column="t2.is_active" />
        <field name="opening.segment" script="getSegment('#{category}')" />
    </entity>


    <!-- DB entity where results should be read by table -->
    <entity name="dbentity" datasource="mysqlConnection">
        <query target="data">
            <![CDATA[
                CREATE TEMP TABLE data AS (
                SELECT *
                FROM table t1 JOIN table t2 ON t1.id = t2.reference
                WHERE t2.creation_time < '#{start_date}')
            ]]>
        </query>
        <field name="id" column="t1.id" />
        <field name="name" column="t1.full_name" />
        <field name="category" column="t2.category" />
        <field name="active" type="boolean" column="t2.is_active" />
        <field name="opening.segment" script="getSegment('#{category}')" />
    </entity>

    <!-- Pig entity -->
    <entity name="dbentity" datasource="pigConnection">
        <query target="output">
            <![CDATA[
                batting = load 'Batting.csv' using PigStorage(',');
                runs = FOREACH batting GENERATE $0 as playerID, $1 as year, $8 as runs;
                grp_data = GROUP runs by (year);
                STORE grp_data INTO 'output';
            ]]>
        </query>
        <field name="id" column="t1.id" />
        <field name="name" column="t1.full_name" />
        <field name="category" column="t2.category" />
        <field name="active" type="boolean" column="t2.is_active" />
        <field name="opening.segment" script="getSegment('#{category}')" />
    </entity>


Sqoop
~~~~~

Tag sqoop instructs import handler to run a Sqoop import. It should be
used only on entities that have a pig datasource. A sqoop tag may
contain the following attributes:

- ``target`` (**required**) the target file to save imported data on HDFS.
- ``datasource`` (**required**) a reference to the DB datasource to use for importing the data
- ``table`` (**required**) the name of the table to import its data.
- ``where`` - an expression that might be passed to the table for filtering the rows to import
- ``direct`` - whether to use direct import (see `Sqoop documentation <https://sqoop.apache.org/docs/1.4.4/SqoopUserGuide.html#_importing_views_in_direct_mode>`_ on --direct for more details)
- ``mappers`` - an integer number with the mappers to use for importing data.If table is a view or doesn't have a key it should be 1. Default value is 1.

If the sqoop tag contains body, then it should be valid SQL statements.
These statements will be executed on the database before the Sqoop
import. This feature is particularly useful if you want to run::

    <entity name="myEntity" datasource="pigConnection">
        <query target="output">
        <![CDATA[
            batting = load 'Batting.csv' using PigStorage(',');
            runs = FOREACH batting GENERATE $0 as playerID, $1 as year, $8 as runs;
            grp_data = GROUP runs by (year);
            STORE grp_data INTO 'output';
        ]]>
        </query>
        <!-- Transfer table dataset to HDFS -->
        <sqoop target="dataset" table="dataset" datasource="sqoop_db_datasource" />

        <!-- Query inside sqoop tag needs to be executed on the DB before running the sqoop command -->
        <!-- We should also allow multiple sqoop tags in case we require more than one imports -->
        <sqoop target="new_data" table="temp_table" datasource="sqoop_db_datasource" direct="true" mappers="1">
        <![CDATA[
            CREATE TEMP TABLE target_openings AS SELECT * FROM openings WHERE creation_time BETWEEN #{start} AND #{end};
            CREATE TABLE temp_table AS SELECT to.*, e.* FROM target_openings to JOIN employer e ON to.employer=e."Record ID#";
        ]]>
        </sqoop>
        <!-- Fields -->
        <field ... />
    </entity>


Nested entities
~~~~~~~~~~~~~~~

It might be possible that not all data required might originate from one
entity, or it might be possible to gather data from more than one
datasources. For example, consider the following use case::

    A really important feature is application ranking.
    In order to rank the application, data regarding the application,
    the employer, the job opening and the contractor are required.
    However, these data may come from different HTTP URLs.


A solution to this problem is to use nested entities. A nested entity is a normal entity, with the benefit that it can use data from it's parent entity to formulate the query. A nested entity may result in two ways:

- querying a 'global' datasource (i.e. querying a different table in DB, calling a different HTTP service)
- converting one of the parent entity's field to a new entity (i.e. parsing the data of a DB column as a JSON document). In this case, the field acts as a datasource.

A nested entity is defined inside another ``<entity>`` and follows exactly the same syntax. However, it might also use the values of parent entity as variables, in addition to the input parameter values.

Example::

    <entity name="application" datasource="ods" query="job_application/pa/#{application}.json">
        <field name="opening" jsonpath="$.result.#{application}.opening_ref" />
        <field name="contractor" jsonpath="$.result.#{application}.developer_ref" />
        <field name="employer" jsonpath="$.result.#{application}.team_ref" />

        <!-- Nested entity using a global datasource -->
        <entity name="opening" datasource="odr" query="opening/f/#{opening}.json">
            <field name="opening.title" jsonpath="$.op_title" />
            <field name="opening.description" jsonpath="$.op_job" />
        </entity>
    </entity>


The second option is to convert one of the parent entity's fields to a
new entity. This is useful if a field in the parent entity contains CSV
or JSON data. To do this, two things need to be done:

- Define property 'transform' in parent entity field, using the appropriate type. This creates a datasource accessible from all child entities. The datasource's name is the field's name, while the datasource type depends on the the value of the transform entity
- In the new entity, define as datasource name the name of the parent entity's field.

Example::

    <!-- Parent entity -->
    <entity name="user" datasource="dbEntity" query="SELECT * FROM users">
        <!-- Convert field to CSV datasource -->
        <field name="permissions" transform="csv" headers="read,write,execute"/>
        <!-- Nested entity using data from CSV field -->
        <entity name="permissionEntity" datasource="permissions">
            <field name="user.read" column="read" />
            <field name="user.execute" column="execute" />
        </entity>

        <
        <!-- Convert field to JSON datasource -->
        <field name="profile" transform="json" />

        <!-- Nested entity using data from JSON field -->
        <entity name="profileEntity" datasource="profile">
            <field name="score" jsonpath="$.score" />
        </entity>
    </entity>

.. _predict:

Predict
-------

The last part of the data import handler describes which models to
invoke and how to formulate the response. While the old import handler
was used with a single model, the new version should allow to use
multiple binary classifier models, provided that they expect the same
input vector.

.. note::

    Predict functionality is not implemented yet.

Response format is defined inside ``<predict>`` tag. Predict tag needs
to have the following sub-elements:

- ``<model>`` - defines parameters for using a model with the data from the ``<import>`` part of the handler
- ``<result>`` - defines how to formulate the response

Model
~~~~~

In order to calculate the result of a prediction, one or more models
need to be invoked together with the data from the import handler. Each
model invocation is defined using a ``<model>`` tag. A model tag may
have the following attributes:

- ``name`` (**required**) - a name to uniquely identify the results of this model
- ``value`` - holds the name of the model to use.
- ``script`` - calls Javascript code to decide the name of the model to use.

.. note::

    Either value or script attribute need to be defined. Declaring none on both should raise an error.

In addition, it should be able to finetune details of model invocation
using some additional child elements: 

positive_label
~~~~~~~~~~~~~~

Allows overriding which label to use as positive label. If not defined, true is considered as positive label. Example::

    <model name="rank" value="BestMatch.v31">
        <positive_label values="false"/>
    </model>
