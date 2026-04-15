"""
Database utility functions for Neo-Sousse 2030
Handles connections, queries, and database operations
"""

import sqlite3
from contextlib import contextmanager
from typing import List, Tuple, Any
import os
from pathlib import Path

# Get project root directory (parent of database folder)
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "neo_sousse.db"


@contextmanager
def get_connection():
    """
    Context manager for database connections.
    Ensures PRAGMA foreign_keys is enabled and proper cleanup.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row  # Access columns by name
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def execute_query(query: str, params: Tuple = ()) -> List[sqlite3.Row]:
    """
    Execute a SELECT query and return results.
    
    Args:
        query: SQL SELECT statement
        params: Query parameters (tuple)
    
    Returns:
        List of Row objects
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_update(query: str, params: Tuple = ()) -> int:
    """
    Execute INSERT/UPDATE/DELETE and return affected rows.
    
    Args:
        query: SQL DML statement
        params: Query parameters (tuple)
    
    Returns:
        Number of affected rows
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.rowcount


def verify_schema() -> bool:
    """
    Verify that all required tables exist.
    
    Returns:
        True if schema is valid, False otherwise
    """
    required_tables = [
        'zones', 'capteurs', 'mesures', 'citoyens', 
        'techniciens', 'vehicules', 'trajets', 'interventions'
    ]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        missing = set(required_tables) - set(existing_tables)
        if missing:
            print(f"Missing tables: {missing}")
            return False
        
        print(f"All {len(required_tables)} tables exist")
        return True


def reset_database():
    """
    Delete the database file for fresh start.
    Use with caution!
    """
    if DB_PATH.exists():
        os.remove(DB_PATH)
        print(f"Database {DB_PATH} deleted")
    else:
        print(f"No database file found at {DB_PATH}")


def get_table_stats():
    """
    Print row counts for all tables.
    """
    tables = ['zones', 'capteurs', 'mesures', 'citoyens', 
              'techniciens', 'vehicules', 'trajets', 'interventions']
    
    print("\nDatabase Statistics:")
    print("-" * 40)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:20} : {count:6} rows")
    print("-" * 40)