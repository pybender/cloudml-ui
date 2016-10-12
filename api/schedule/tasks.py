import os
import json
import logging
import numpy
import csv
import uuid
from itertools import izip, repeat
from sqlalchemy.exc import SQLAlchemyError

from api import celery, app
from api.base.tasks import SqlAlchemyTask, TaskException, get_task_traceback
from api.base.exceptions import InvalidOperationError
from celery import task, chain, chord, group
from celery.utils.log import get_logger, get_task_logger
from api.model_tests.models import TestResult, TestExample
from api.schedule.models import (PeriodicTaskScenarios, PeriodicTasks, PeriodicTask)

logger = get_logger(__name__)

class InstanceRequestingError(TaskException):
    pass

class TaskScenario(object):
    name = None

    def __init__(self, name, payload):
        self.name = name
        self.payload = payload

    def load(self):
        pass

    def save(self):

        pass

    @property
    def steps(self):

        return 12

    def __str__(self):
        fmt = '{0.name}: {0.steps}'
        return fmt.format(self)

@celery.task(base=SqlAlchemyTask)
def test_chord_01(*args, **kwargs):
    tasklog = get_task_logger(__name__)
    logger.info('chord 01')
    return 11

@celery.task(base=SqlAlchemyTask)
def test_chord_02(*args, **kwargs):
    tasklog = get_task_logger(__name__)
    logger.info('chord 02')
    return 12

@celery.task(base=SqlAlchemyTask)
def test_chord_03(*args, **kwargs):
    tasklog = get_task_logger(__name__)
    logger.info('chord 03')
    return 13

@celery.task(base=SqlAlchemyTask)
def test_task_01(*args, **kwargs):
    logger.info('task 01')
    print("single:", args, kwargs)
    return 21

@celery.task(base=SqlAlchemyTask)
def test_single_01(*args, **kwargs):
    tasklog = get_task_logger(__name__)
    logger.info('single 01')
    return 31


@celery.task(base=SqlAlchemyTask)
@app.regscheduletask()
def test_schedule_task():
    tasklog = get_task_logger(__name__)
    tasklog.debug('Start...')

    logger.debug('Test %s completed.' % 'test_schedule_task')
    return 'test_schedule_task completed'

@celery.task(base=SqlAlchemyTask)
@app.regscheduletask()
def test_schedule_task_01():
    logger.debug('Test %s start...' % 'test_schedule_task_01')

    logger.debug('Test %s completed.' % 'test_schedule_task_01')


@celery.task(base=SqlAlchemyTask)
@app.regscheduletask()
def scenarios_schedule_task(*args, **kwargs):
    taskid = kwargs.get('task', None)
    if taskid:
        try:
            taskid = int(taskid)
            logger.info('Task %s start...' % taskid)
            task = PeriodicTaskScenarios.query.filter_by(id=taskid).first()
            if task:
                scenario = TaskScenario(task.name, task.scenarios)
                print (scenario)
                logger.info('Task end.')
                return 'Completed'

        except Exception as e:
            logger.error('Error get scenarios task  id: %s .' % taskid)
            print ("Error", e)
    else:
        logger.info('No task enter')

    return 'Error.GetTask'

