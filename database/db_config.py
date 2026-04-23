"""
PostgreSQL Database Configuration
"""
import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
DB_NAME = os.getenv('DB_NAME', 'neo_sousse_2030')
DB_PORT = os.getenv('DB_PORT', '5432')

def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )