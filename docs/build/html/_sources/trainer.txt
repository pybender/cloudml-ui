.. _trainer:

=======
Trainer
=======

System stores pickled Trainer class for the model in Amazon S3.
Trainer could use the configuration defined in model features and perform the training of the classifier. The trainer can also perform testing of the generated model. 

The user will be able to either define datasets containing data to be used for training and testing the classifier, or
specify the required parameters to invoke the import handler and retrieve the data.

The underlying implementation supporting the trainer is based on Python's `scikit-learn <http://scikit-learn.org>`_ package.

.. note::

    You could load already trained model by specify trainer file in the `upload model page <http://cloudml.int.odesk.com/#/upload_model>`_