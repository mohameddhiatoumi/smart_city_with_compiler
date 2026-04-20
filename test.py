import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from database.db_utils import execute_query

print("=" * 60)
print("🔍 CHECKING SENSOR DATA IN DATABASE")
print("=" * 60 + "\n")

# Check what's in the capteurs table
result = execute_query("""
    SELECT 
        capteur_id,
        type_capteur,
        statut,
        taux_erreur,
        nb_anomalies_totales
    FROM capteurs
    LIMIT 5
""", ())

print("📊 First 5 sensors in DB:")
for row in result:
    print(f"   {row['capteur_id']:10s} | Type: {row['type_capteur']:8s} | Status: {row['statut']:15s} | Error: {row['taux_erreur']} | Anomalies: {row['nb_anomalies_totales']}")

print("\n" + "=" * 60)