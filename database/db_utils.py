"""
Database utility functions for Neo-Sousse 2030
Handles connections, queries, and database operations
UPDATED: PostgreSQL version
"""

import psycopg2
from contextlib import contextmanager
from typing import List, Dict, Any, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ CHANGE 1: PostgreSQL configuration from .env
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'neo_sousse_2030')
DB_PORT = os.getenv('DB_PORT', '5432')


@contextmanager
def get_connection():
    """
    Context manager for PostgreSQL database connections.
    Ensures proper cleanup and error handling.
    """
    conn = None
    try:
        # ✅ CHANGE 2: PostgreSQL connection
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def execute_query(query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
    """
    Execute a SELECT query and return results as list of dicts.
    
    Args:
        query: SQL SELECT statement (use %s for placeholders, not ?)
        params: Query parameters (tuple)
    
    Returns:
        List of dictionaries
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        # ✅ CHANGE 3: Get column names for dict conversion
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        results = []
        for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
        
        cursor.close()
        return results


def execute_update(query: str, params: Tuple = ()) -> int:
    """
    Execute INSERT/UPDATE/DELETE and return affected rows.
    
    Args:
        query: SQL DML statement (use %s for placeholders)
        params: Query parameters (tuple)
    
    Returns:
        Number of affected rows
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rowcount = cursor.rowcount
        cursor.close()
        return rowcount


def verify_schema() -> bool:
    """
    Verify that all required tables exist.
    
    Returns:
        True if schema is valid, False otherwise
    """
    required_tables = [
        'zones', 'capteurs', 'mesures', 'citoyens', 
        'techniciens', 'vehicules', 'trajets', 'interventions', 'alertes'
    ]
    
    with get_connection() as conn:
        cursor = conn.cursor()
        # ✅ CHANGE 4: PostgreSQL system catalog query
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        missing = set(required_tables) - set(existing_tables)
        if missing:
            print(f"❌ Missing tables: {missing}")
            return False
        
        print(f"✅ All {len(required_tables)} tables exist")
        return True


def get_table_stats():
    """
    Print row counts for all tables.
    """
    tables = ['zones', 'capteurs', 'mesures', 'citoyens', 
              'techniciens', 'vehicules', 'trajets', 'interventions', 'alertes']
    
    print("\n📊 Database Statistics:")
    print("-" * 50)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        for table in tables:
            # ✅ CHANGE 5: Use %s for PostgreSQL
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"{table:20} : {count:6} rows")
        cursor.close()
    
    print("-" * 50)