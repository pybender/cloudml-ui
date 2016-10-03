import os
import logging
import numpy
import csv
import uuid
from itertools import izip, repeat
from sqlalchemy.exc import SQLAlchemyError

from api import celery, app
from api.base.tasks import SqlAlchemyTask, TaskException, get_task_traceback
from api.base.exceptions import InvalidOperationError
from celery.utils.log import get_logger
from api.model_tests.models import TestResult, TestExample

logger = get_logger(__name__)

@celery.task(base=SqlAlchemyTask)
@app.regscheduletask()
def test_schedule_task():
    logger.debug('Test %s start...' % 'test_schedule_task')


    logger.debug('Test %s completed.' % 'test_schedule_task')
    return 'test_schedule_task completed'

@celery.task(base=SqlAlchemyTask)
@app.regscheduletask()
def test_schedule_task_01():
    logger.debug('Test %s start...' % 'test_schedule_task_01')


    logger.debug('Test %s completed.' % 'test_schedule_task_01')
    return 'test_schedule_task_01 completed '