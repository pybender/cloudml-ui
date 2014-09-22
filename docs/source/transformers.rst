********-+.. _transforrmers:

=======================
Pretrained transformers
=======================

Cloudml have possibility to define and train transformers without train model.
Trained transformers stored to amazon s3 to folder wich defined in settings.

For train transformers you can use import handlers and imported datasets as for train models.


===============================
Transformer JSON file format
===============================

An example of such file is the following::

	{
	  "transformer-name": "bestmatch",
	  "field-name": "contractor.dev_title",
	  "type": "text",
	  "transformer":{
	        "type": "Tfidf",
	        "params": {
	          	"ngram_range_min": 1,
	          	"ngram_range_max": 1,
	          	"min_df": 5
	          	}
	      }
	}


"field-name" is field which will be use for train transformer.
"type" is type of field.

Available transformer types:

 - Dictionary
 - Count
 - Tfidf
 - Lda
 - Lsi
 - Ntile


You can run the train transformer using::

	python transformer.py [-h] [-V] [-o output] [-i input-file] [-e extraction-plan-file] [-I train-param] path

The detials of the parameters passed to trainer.py are the following:


+-----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Paramete-+++++++++r                         | Description                                                                                                                                                                                                                       |
+===================================+===================================================================================================================================================================================================================================+
| -h, --help                        | Prints help message                                                                                                                                                                                                               |
+-----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| -V, --version                     | Prints version message                                                                                                                                                                                                            |
+-----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| -o output, --output output        | Saves trained transformer and related data to this file.                                                                                                                                                                          |
+-----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| -i input-data, --input input-data | Read train data from file 'input-data'. Input file may contain multiple JSON objects, each one containing the feature data for each row data.                                                                                     |
+-----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| -e extraction-plan                | Use the extraction plan defined in the given path. If -i has been defined, it will be ignored.                                                                                                                                    |
+-----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| -I key=value                      | Allows user defined parameters. The given parameters will be used to replace parameters in the SQL query. Can have multiple values. Will be used only if flag -e is defined. These values will be used for extracting train data. |
+-----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| path                              | Path pointing to transformer.json configuration file.                                                                                                                                                                             |
+-----------------------------------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


Train transformer using existing data::

	$ python transformer.py ./testdata/transformers/transformer.json -i ./testdata/transformers/train.data.json 
