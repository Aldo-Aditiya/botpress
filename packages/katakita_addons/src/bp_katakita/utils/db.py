import os
import psycopg2
import pymongo

from chat_assistant.app.utils.mongodb import load_collection

from bp_katakita.config import load_config

# ----------------- #

CONFIG = load_config()

# Connect to the database
DB_CONFIG = CONFIG["DATABASE"]
APP_DB_NAME = CONFIG["CHAT_HISTORY_DB"]["name"]
APP_DB_PARAMS = CONFIG["CHAT_HISTORY_DB"]["params"]
APP_DB_COLLECTION_NAME = CONFIG["CHAT_HISTORY_DB"]["collections"]["chat_history"]

collection = load_collection(APP_DB_NAME, APP_DB_PARAMS, APP_DB_COLLECTION_NAME)

# ----------------- #

# Postgres

def connect_postgres_db():
    db_conn = psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["name"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"]
    )
    return db_conn

def close_postgres_db(db_conn):
    db_conn.close()

def read_postgres_db(query:str):

    db_conn = connect_postgres_db()
    try:
        db_cursor = db_conn.cursor()
        db_cursor.execute(query)
        result = db_cursor.fetchall()

        db_cursor.close()

        return result
    finally:
        close_postgres_db(db_conn)

def write_postgres_db(query:str):

    db_conn = connect_postgres_db()
    try:
        db_cursor = db_conn.cursor()
        db_cursor.execute(query)
        db_conn.commit()

        db_cursor.close()
    finally:
        close_postgres_db(db_conn)