"""
Test PostgreSQL connection and FSM Manager
"""
import os
from dotenv import load_dotenv
from database.db_config import get_db_connection
from fsm_engine import FSMManager

load_dotenv()

print("🧪 Testing PostgreSQL Connection...")
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM zones")
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    print(f"✅ PostgreSQL Connection OK - Found {count} zones")
except Exception as e:
    print(f"❌ Connection Error: {e}")
    exit(1)

print("\n🧪 Testing FSM Manager...")
try:
    fsm_manager = FSMManager(None)  # db_path not needed for this test
    print("✅ FSM Manager initialized")
except Exception as e:
    print(f"❌ FSM Manager Error: {e}")
    exit(1)

print("\n✅ All tests passed! Ready to run the application.")