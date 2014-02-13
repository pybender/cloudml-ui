.. _json_changes:

====================
Migrating JSON files
====================

Features
--------
Please migrate features file by wrapping entity parameters to `params` section.

So you need to do it with:

* classifier
* all feature transformers
* all feature scalers


For example::

  "classifier": {
    "type": "logistic regression",
    "penalty": "l2"
  }

should be changed to::

  "classifier": {
    "type": "logistic regression",
    "params": {"penalty": "l2"}
  }

.. note::

    Parameters of name feature types was wrapped with `params` before, so no changes here needed.


Import Handler
--------------
For migrating import handler file you need to make some changes.

In queries -> items:

* ``is-required`` renamed to ``is_required``
* ``process-as`` renamed to ``process_as``
* ``target-features`` renamed to ``target_features``

In queries -> items -> target_features:

* ``key-path`` renamed to ``key_path``
* ``value-path`` renamed to ``value_path``
* ``to-csv`` renamed to ``to_csv``
