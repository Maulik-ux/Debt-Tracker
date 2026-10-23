import sqlite3
import os
from config import Config

def get_connection():
    """
    Establishes and returns a connection to the SQLite database.
    Enforces PRAGMA foreign_keys = ON for referential integrity.
    """
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    # Technique: Parameterised CRUD & Foreign Key Enforcement
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initializes the database schema using schema.sql."""
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    if os.path.exists(schema_path):
        conn = get_connection()
        with open(schema_path, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()