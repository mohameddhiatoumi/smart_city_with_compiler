import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent))

from database.db_utils import execute_query

time_threshold = datetime.now() - timedelta(hours=1)
time_threshold_str = time_threshold.strftime('%Y-%m-%d %H:%M:%S')

print(f"Time threshold: {time_threshold_str}")
print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Test 1: Count measurements from last 1 hour
query1 = """
    SELECT COUNT(*) as count FROM mesures
    WHERE timestamp >= ?
"""
result1 = execute_query(query1, (time_threshold_str,))
print(f"\n1️⃣  Measurements from last 1 hour: {result1[0]['count']}")

# Test 2: Count active sensors
query2 = """
    SELECT COUNT(*) as count FROM capteurs
    WHERE statut IN ('actif', 'signale')
"""
result2 = execute_query(query2, ())
print(f"2️⃣  Active/signaled sensors: {result2[0]['count']}")

# Test 3: The EXACT query from the API
query3 = """
    SELECT 
        mesure_id, 
        capteur_id, 
        timestamp, 
        type_mesure, 
        valeur, 
        unite, 
        est_anomalie
    FROM mesures
    WHERE timestamp >= ?
    AND capteur_id IN (
        SELECT capteur_id FROM capteurs 
        WHERE statut IN ('actif', 'signale')
    )
    ORDER BY timestamp DESC
    LIMIT ?
"""
result3 = execute_query(query3, (time_threshold_str, 500))
print(f"\n3️⃣  EXACT API QUERY result count: {len(result3) if result3 else 0}")

if result3 and len(result3) > 0:
    print(f"\n✅ First 5 results:")
    for i, row in enumerate(result3[:5]):
        print(f"  {i+1}. {dict(row)}")
else:
    print("\n❌ No results from EXACT API query!")
    
    # Debug: Check raw data
    print("\n🔍 Debugging - checking raw timestamps:")
    query_debug = "SELECT timestamp FROM mesures ORDER BY timestamp DESC LIMIT 5"
    debug_result = execute_query(query_debug, ())
    for row in debug_result:
        print(f"  Raw timestamp: '{row['timestamp']}' (type: {type(row['timestamp'])})")