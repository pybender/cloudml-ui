.. _instances:

*********
Instances
*********

Instance - it's a Amazon EC2 instance with runned celery worker.
Now two types of the instances used in the system:

- On-Demand Instances
- Spot Instances

.. note::

    Now system supports only training in different types of instances. Model testing always will run on main celery worker.

`Here <http://aws.amazon.com/ec2/instance-types/>`_ could be found the specifications for each Amazon EC2 Instance Type.

.. _on-demand_instances:

On-Demand Instances
-------------------

List of the On-Demand Instances could be found in `the instance list page <http://cloudml.int.odesk.com/#/aws/instances/>`_.

.. _spot_instances:

Spot Instances
--------------
 
System could use `Amazon EC2 Spot Instances <http://aws.amazon.com/ec2/purchasing-options/spot-instances/>`_ for traing model.
