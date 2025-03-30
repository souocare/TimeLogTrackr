# db.py

import sqlite3

DB_PATH = "pATH TO tasks.db"

def get_connection():
    """
    Establishes and returns a connection to the SQLite database.

    Returns:
        sqlite3.Connection: An active database connection with WAL mode enabled.

    Notes:
        - Write-Ahead Logging (WAL) mode is used to allow for concurrent reads and writes.
        - Timeout is set to 10 seconds.
        - check_same_thread=False allows connection sharing across threads.
    """
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def initialize_database():
    """
    Initializes the database by creating the 'tasks' table if it doesn't exist.

    Table schema:
        - id: Unique ID for each task entry.
        - name: Name of the task.
        - start_time: When the task started (can be NULL).
        - end_time: When the task ended (can be NULL).
        - total_time: Total accumulated time in seconds (can be negative for corrections).
        - status: Task status (e.g., 'paused', 'running', 'correction').
        - date: Date string (YYYY-MM-DD) used for daily tracking.

    This function ensures the database is ready for use at application startup.
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
