# db.py

import sqlite3

DB_PATH = "C:\\Users\\Goncalo\\Desktop\\TaskMngmTool\\tasks.db"

def get_connection():
    """
    Creates and returns a SQLite connection with Write-Ahead Logging (WAL) mode enabled
    to improve concurrency and avoid database locking.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def initialize_database():
    """
    Initializes the database by creating the 'tasks' table if it doesn't already exist.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            total_time INTEGER DEFAULT 0,
            status TEXT,
            date TEXT
        )
    """)
    conn.commit()
    conn.close()
