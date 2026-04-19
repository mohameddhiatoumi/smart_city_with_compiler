"""
Reset all sensors to baseline values with random status distribution
Clears anomalies and assigns realistic sensor statuses
"""

import sys
import random
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from database.db_utils import get_connection
from simulator_config import MEASUREMENT_BASELINES

def reset_sensors_with_distribution():
    """Reset all sensors with realistic status distribution"""
    print("\n" + "="*60)
    print("🔄 RESETTING ALL SENSORS WITH STATUS DISTRIBUTION")
    print("="*60 + "\n")
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Delete all measurements
        cursor.execute("DELETE FROM mesures")
        deleted_count = cursor.rowcount
        print(f"✅ Deleted {deleted_count} measurements")
        
        # Get all sensors
        cursor.execute("SELECT capteur_id FROM capteurs")
        all_sensors = [row['capteur_id'] for row in cursor.fetchall()]
        total_sensors = len(all_sensors)
        
        # Distribution percentages
        ACTIF_PERCENT = 0.60      # 60% active
        SIGNALE_PERCENT = 0.15    # 15% flagged
        EN_MAINTENANCE_PERCENT = 0.15  # 15% in maintenance
        HORS_SERVICE_PERCENT = 0.10    # 10% out of service
        
        # Calculate counts
        actif_count = int(total_sensors * ACTIF_PERCENT)
        signale_count = int(total_sensors * SIGNALE_PERCENT)
        en_maintenance_count = int(total_sensors * EN_MAINTENANCE_PERCENT)
        hors_service_count = total_sensors - actif_count - signale_count - en_maintenance_count
        
        # Shuffle and assign statuses
        random.shuffle(all_sensors)
        
        status_assignments = []
        idx = 0
        
        # Assign 'actif'
        for i in range(actif_count):
            status_assignments.append((all_sensors[idx], 'actif'))
            idx += 1
        
        # Assign 'signale'
        for i in range(signale_count):
            status_assignments.append((all_sensors[idx], 'signale'))
            idx += 1
        
        # Assign 'en_maintenance'
        for i in range(en_maintenance_count):
            status_assignments.append((all_sensors[idx], 'en_maintenance'))
            idx += 1
        
        # Assign 'hors_service'
        for i in range(hors_service_count):
            status_assignments.append((all_sensors[idx], 'hors_service'))
            idx += 1
        
        # Update all sensors
        for sensor_id, status in status_assignments:
            cursor.execute("""
                UPDATE capteurs
                SET taux_erreur = 0,
                    nb_anomalies_totales = 0,
                    statut = ?
                WHERE capteur_id = ?
            """, (status, sensor_id))
        
        # Print distribution
        print("\n📊 SENSOR STATUS DISTRIBUTION:")
        print(f"  🟢 Actif (Active):        {actif_count:3d} sensors ({ACTIF_PERCENT*100:.0f}%)")
        print(f"  🟡 Signalé (Flagged):     {signale_count:3d} sensors ({SIGNALE_PERCENT*100:.0f}%)")
        print(f"  🔧 En Maintenance:        {en_maintenance_count:3d} sensors ({EN_MAINTENANCE_PERCENT*100:.0f}%)")
        print(f"  🔴 Hors Service (Out):    {hors_service_count:3d} sensors ({HORS_SERVICE_PERCENT*100:.0f}%)")
        print(f"  ─────────────────────────────")
        print(f"  📈 Total:                 {total_sensors:3d} sensors")
        
        # Verify
        cursor.execute("""
            SELECT statut, COUNT(*) as count
            FROM capteurs
            GROUP BY statut
            ORDER BY statut
        """)
        print("\n✅ VERIFICATION:")
        for row in cursor.fetchall():
            print(f"   {row['statut']:20s}: {row['count']:3d} sensors")
    
    print("\n" + "="*60)
    print("🎉 ALL SENSORS RESET AND DISTRIBUTED!")
    print("="*60)
    print("\nNow run: python simulator/sensor_simulator.py\n")

if __name__ == "__main__":
    reset_sensors_with_distribution()