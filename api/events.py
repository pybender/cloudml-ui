from sqlalchemy import event
from sqlalchemy.engine import Engine
import time
import logging
 
logging.basicConfig()
logger = logging.getLogger("cloudml.sqltime")
logger.setLevel(logging.DEBUG)


@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, 
                          parameters, context, executemany):
    context._query_start_time = time.time()
    logger.debug("\n\n\nStart Query: %s" % statement)
    logger.debug("Parameters:\n%r" % (parameters, ))


@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, 
                         parameters, context, executemany):
    total = time.time() - context._query_start_time
    logger.debug("Query Complete!")
    logger.debug("Total Time: %f" % total)
