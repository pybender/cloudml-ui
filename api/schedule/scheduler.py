from api import celery
from celery.utils.log import get_logger
from beatsqlalchemy.schedulers import DatabaseScheduler

logger = get_logger(__name__)

class CloudmluiDatabaseScheduler(DatabaseScheduler):
    def __init__(self, session=None, *args, **kwargs):
        logger.info("Start Cloudmlui celery beat database scheduler...")
        super(CloudmluiDatabaseScheduler, self).__init__(*args, **kwargs)
