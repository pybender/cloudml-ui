import psycopg2
from psycopg2.extras import DictCursor

from api import app


_conn = None


def get_connection():
    global _conn
    if not _conn:
        _conn = psycopg2.connect(app.config['DB_CONNECTION_STRING'])
    return _conn


def select(sql, params):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(sql, params)
    return cursor


def execute(sql, params):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute(sql, params)
    cursor.close()


def commit():
    get_connection().commit()
