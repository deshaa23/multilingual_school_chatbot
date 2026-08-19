import psycopg
from backend.config import db_config
from psycopg.rows import dict_row
from contextlib import contextmanager

def get_connection():
    return psycopg.connect(**db_config)

def fetch_all(query, params=None):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()
        
def fetch_one(query, params=None):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        
def execute_query(query, params=None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params or ())
            affected_rows = cursor.rowcount
            conn.commit()
            return affected_rows
        
def execute_returning(query, params=None):
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, params or())
            result = cursor.fetchone()
            conn.commit()
            return result
        
@contextmanager
def get_db():
    conn=get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()